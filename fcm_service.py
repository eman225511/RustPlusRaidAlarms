"""
FCM Service - Direct Rust+ notification monitoring via Firebase Cloud Messaging
"""

import threading
import webbrowser
import time
import json
import os
import shutil
import subprocess
import requests
import multiprocessing
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from flask import Flask, request
import multiprocessing
from datetime import datetime

# Lazy imports to avoid errors if not installed
FCMListener = None
RustSocket = None
ServerDetails = None

def fcm_listener_worker(fcm_credentials, notification_queue=None):
    """Module-level worker used as a multiprocessing target.
    Runs the rustplus FCMListener and keeps the process alive.
    """
    def dbg(msg):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [FCM worker][pid={os.getpid()}] {msg}")

    try:
        from rustplus import FCMListener
        import time

        def on_notification(obj, notification, data_message):
            # Send notification to main service via queue
            if notification_queue:
                try:
                    notification_queue.put((obj, notification, data_message))
                except Exception as e:
                    dbg(f"Failed to send notification to queue: {e}")
            
            # Summarize notification for logs
            try:
                nid = None
                data = None
                if hasattr(data_message, 'data'):
                    data = data_message.data
                    if isinstance(data, dict):
                        nid = data.get('persistent_id') or data.get('id')

                # Fallback: try extracting from notification dict
                if nid is None and isinstance(notification, dict):
                    nid = notification.get('persistent_id') or notification.get('id')
                    if nid is None and 'body' in notification:
                        try:
                            body_json = json.loads(notification['body'])
                            nid = body_json.get('id') or body_json.get('persistent_id')
                        except Exception:
                            pass

                # Log notification
                if nid is None:
                    try:
                        dbg(f"Notification received body_id=None; notification={notification}; data={json.dumps(data, default=str)}")
                    except Exception:
                        dbg(f"Notification received body_id=None; notification={notification}; data_repr={repr(data)}")
                else:
                    dbg(f"Notification received body_id={nid}")

            except Exception as _:
                dbg("Notification received (unable to summarize)")

        dbg("Starting FCMListener")
        listener = FCMListener(data={"fcm_credentials": fcm_credentials})
        listener.on_notification = on_notification
        listener.start(daemon=False)
        dbg("FCMListener started; entering wait loop")
        # Keep process alive while listener thread runs
        while True:
            time.sleep(1)
    except Exception as exc:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [FCM worker][pid={os.getpid()}] ERROR: {exc}")


class FCMService(QThread):
    """
    FCM service for direct Rust+ notifications
    Emits signals that plugins can connect to
    """
    
    message_received = Signal(str)  # Emitted when filtered notification arrives
    status_changed = Signal(str, str)  # status text, color
    running_changed = Signal(bool)  # Emitted when listener starts/stops
    auth_completed = Signal(bool, str)  # success, message
    server_paired = Signal(str, str)  # server_name, server_ip:port
    
    CALLBACK_PORT = 43721
    TOKEN_FILE = "rustplus_token.json"
    CONFIG_FILE = "rustplus.config.json"
    SEEN_FILE = "seen_notifications.json"
    PAIRING_FILE = "fcm_pairing.json"
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = False
        self.fcm_listener = None
        self.fcm_listener_process = None
        self.notification_queue = multiprocessing.Queue()
        self.auth_done = threading.Event()
        self.rustplus_token = None
        self.steam_id = None
        self.fcm_credentials = None
        self.seen_notifications = set()
        self.flask_app = None
        self.flask_thread = None
        self.notification_count = 0
        self.paired_server_id = None
        self.paired_server_name = None
        self.paired_server_ip = None
        self.paired_server_port = None
        
        # Load existing credentials if available
        self.load_credentials()
        self.load_seen_notifications()
        self.load_pairing()

    def load_credentials(self):
        """Load existing auth token, FCM credentials, and filter keyword"""
        try:
            # Load auth token
            if os.path.exists(self.TOKEN_FILE):
                with open(self.TOKEN_FILE, "r") as f:
                    token_data = json.load(f)
                    self.rustplus_token = token_data.get("token")
                    self.steam_id = token_data.get("steam_id")
                    print(f"[FCM] Loaded auth token for Steam ID: {self.steam_id}")
            # Load FCM credentials and filter keyword
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.fcm_credentials = config.get("fcm_credentials")
                    # Prefer refreshed auth token if present
                    cli_token = config.get("rustplus_auth_token")
                    if cli_token:
                        self.rustplus_token = cli_token
                    # Load filter keyword if present
                    filter_kw = config.get("fcm_filter_keyword")
                    if filter_kw is not None:
                        self.config["fcm_filter_keyword"] = filter_kw
                    print("[FCM] Loaded rustplus.js config")
        except Exception as e:
            print(f"[FCM] Error loading credentials: {e}")
    
    def load_seen_notifications(self):
        """Load previously seen notification IDs from file"""
        try:
            if os.path.exists(self.SEEN_FILE):
                with open(self.SEEN_FILE, "r") as f:
                    seen_list = json.load(f)
                    self.seen_notifications = set(seen_list)
                    print(f"[FCM] Loaded {len(self.seen_notifications)} previously seen notifications")
        except Exception as e:
            print(f"[FCM] Error loading seen notifications: {e}")
            self.seen_notifications = set()
    
    def save_seen_notification(self, notif_id):
        """Add notification ID to seen set and save to file"""
        self.seen_notifications.add(notif_id)
        try:
            with open(self.SEEN_FILE, "w") as f:
                json.dump(list(self.seen_notifications), f, indent=2)
        except Exception as e:
            print(f"[FCM] Failed to save seen notification: {e}")
    
    def load_pairing(self):
        """Load server pairing information"""
        try:
            if os.path.exists(self.PAIRING_FILE):
                with open(self.PAIRING_FILE, "r") as f:
                    pairing_data = json.load(f)
                    self.paired_server_id = pairing_data.get("server_id")
                    self.paired_server_name = pairing_data.get("server_name", "Unknown Server")
                    self.paired_server_ip = pairing_data.get("server_ip")
                    self.paired_server_port = pairing_data.get("server_port")
                    print(f"[FCM] Loaded pairing for: {self.paired_server_name} ({self.paired_server_ip}:{self.paired_server_port})")
        except Exception as e:
            print(f"[FCM] Error loading pairing: {e}")
    
    def save_pairing(self, server_id, server_name, server_ip, server_port, player_id=None, player_token=None):
        """Save server pairing information"""
        try:
            pairing_data = {
                "server_id": server_id,
                "server_name": server_name,
                "server_ip": server_ip,
                "server_port": server_port,
                "player_id": player_id,
                "player_token": player_token,
                "paired_at": time.time()
            }
            with open(self.PAIRING_FILE, "w") as f:
                json.dump(pairing_data, f, indent=2)
            
            self.paired_server_id = server_id
            self.paired_server_name = server_name
            self.paired_server_ip = server_ip
            self.paired_server_port = server_port
            
            print(f"[FCM] Saved pairing for: {server_name} ({server_ip}:{server_port})")
            self.server_paired.emit(server_name, f"{server_ip}:{server_port}")
        except Exception as e:
            print(f"[FCM] Failed to save pairing: {e}")
    
    def delete_pairing(self):
        """Delete server pairing"""
        try:
            if os.path.exists(self.PAIRING_FILE):
                os.remove(self.PAIRING_FILE)
            self.paired_server_id = None
            self.paired_server_name = None
            self.paired_server_ip = None
            self.paired_server_port = None
            print(f"[FCM] Deleted server pairing")
            self.server_paired.emit("", "")
            return True
        except Exception as e:
            print(f"[FCM] Failed to delete pairing: {e}")
            return False
    
    def is_paired(self):
        """Check if paired with a server"""
        return self.paired_server_id is not None
    
    def is_authenticated(self):
        """Check if user is authenticated and FCM credentials exist"""
        return (
            self.rustplus_token is not None and 
            self.steam_id is not None and 
            self.fcm_credentials is not None and
            os.path.exists(self.TOKEN_FILE) and
            os.path.exists(self.CONFIG_FILE)
        )
    
    def start_auth_flow(self):
        """Start the authentication flow in a separate thread"""
        auth_thread = threading.Thread(target=self._run_auth_flow, daemon=True)
        auth_thread.start()
    
    def _run_auth_flow(self):
        """Run the complete authentication flow"""
        try:
            self.status_changed.emit("Starting authentication...", "#ffa500")
            
            # Setup Flask callback server
            self._setup_flask_app()
            
            # Start Flask server in background
            self.flask_thread = threading.Thread(
                target=self._run_flask_server, 
                daemon=True
            )
            self.flask_thread.start()
            
            # Give Flask a moment to start
            time.sleep(1)
            
            # Open browser for Steam login
            login_url = (
                "https://companion-rust.facepunch.com/login"
                f"?returnUrl=http://localhost:{self.CALLBACK_PORT}/callback"
            )
            
            self.status_changed.emit("Opening browser for Steam login...", "#ffa500")
            print("[FCM] Opening browser for Steam login...")
            webbrowser.open(login_url)
            
            # Wait for callback (with timeout)
            self.status_changed.emit("Waiting for Steam login...", "#ffa500")
            auth_success = self.auth_done.wait(timeout=300)  # 5 minute timeout
            
            if not auth_success:
                self.status_changed.emit("❌ Authentication timeout", "#ff4444")
                self.auth_completed.emit(False, "Authentication timed out after 5 minutes")
                return
            
            if not self.rustplus_token:
                self.status_changed.emit("❌ No token received", "#ff4444")
                self.auth_completed.emit(False, "Failed to receive authentication token")
                return
            
            # Save token
            with open(self.TOKEN_FILE, "w") as f:
                json.dump({
                    "token": self.rustplus_token,
                    "steam_id": self.steam_id
                }, f, indent=2)
            
            self.status_changed.emit("Setting up FCM credentials...", "#ffa500")
            
            # Setup FCM credentials
            if not self._setup_fcm_credentials():
                self.status_changed.emit("❌ FCM setup failed", "#ff4444")
                self.auth_completed.emit(False, "Failed to setup FCM credentials. Check Node.js installation.")
                return
            
            # Reload credentials
            self.load_credentials()
            
            # Register device for push
            self._register_device_for_push()
            
            self.status_changed.emit("✓ Authentication complete!", "#00ff00")
            self.auth_completed.emit(True, "Authentication successful! You can now start FCM mode.")
            
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            print(f"[FCM] {error_msg}")
            self.status_changed.emit(f"❌ {error_msg}", "#ff4444")
            self.auth_completed.emit(False, error_msg)
    
    def _setup_flask_app(self):
        """Setup Flask app for OAuth callback"""
        self.flask_app = Flask(__name__)
        
        @self.flask_app.route("/callback")
        def callback():
            self.rustplus_token = request.args.get("token")
            self.steam_id = request.args.get("steamId")
            
            if not self.rustplus_token:
                return "No token received", 400
            
            print(f"[FCM] Auto-detected Steam ID: {self.steam_id}")
            self.auth_done.set()
            
            try:
                self.status_changed.emit("Starting FCM listener...", "#ffa500")
                print("[FCM] Starting FCM listener (subprocess)...")
                self.fcm_listener_process = multiprocessing.Process(
                    target=fcm_listener_worker,
                    args=(self.fcm_credentials, self.notification_queue)
                )
                self.fcm_listener_process.start()
                self.status_changed.emit("✓ FCM listener active", "#00ff00")
                print("[FCM] FCM listener subprocess started and waiting for notifications...")
                while self.running:
                    time.sleep(1)
            except Exception as e:
                error_msg = str(e)
                print(f"[FCM] Error: {error_msg}")
                self.status_changed.emit(f"❌ Error: {error_msg[:50]}", "#ff4444")
            finally:
                self.running = False
                if self.fcm_listener_process:
                    if self.fcm_listener_process.is_alive():
                        self.fcm_listener_process.terminate()
                        self.fcm_listener_process.join(timeout=2)
                try:
                    print("[FCM] Running custom FCM helper...")
                    scripts_dir = os.path.join(os.getcwd(), "scripts")
                    package_json = os.path.join(scripts_dir, "package.json")
                    
                    # Install npm dependencies
                    npm_path = shutil.which("npm") or "npm"
                    if os.path.exists(package_json):
                        print("[FCM] Installing npm dependencies...")
                        subprocess.run([npm_path, "install"], cwd=scripts_dir, 
                                     capture_output=True, timeout=60)
                    
                    # Locate node executable
                    node_path = shutil.which("node") or "node"

                    # Run custom FCM setup
                    result = subprocess.run([
                        node_path,
                        os.path.join(scripts_dir, "fcm_setup_custom.js"),
                        "--auth-token",
                        self.rustplus_token,
                        "--config",
                        self.CONFIG_FILE,
                    ], cwd=os.getcwd(), capture_output=True, timeout=60)
                    
                    if result.returncode == 0 and os.path.exists(self.CONFIG_FILE):
                        print("[FCM] Custom FCM helper completed.")
                        return True
                    else:
                        print(f"[FCM] Custom helper failed: {result.stderr.decode()}")
                except Exception as e:
                    print(f"[FCM] Custom helper error: {e}")
            
            # Fallback to official CLI
            npx_path = shutil.which("npx")
            if npx_path:
                print("[FCM] Running rustplus.js CLI (fcm-register)...")
                result = subprocess.run([
                    npx_path,
                    "@liamcottle/rustplus.js",
                    "--config-file",
                    self.CONFIG_FILE,
                    "fcm-register",
                ], cwd=os.getcwd(), capture_output=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(self.CONFIG_FILE):
                    print("[FCM] rustplus.js config created.")
                    return True
                else:
                    print(f"[FCM] CLI failed: {result.stderr.decode()}")
            
            print("[FCM] Node/npx not found; FCM setup failed.")
            return False

    def _register_device_for_push(self):
        """Register device for push notifications"""
        try:
            # Load expo push token from config
            with open(self.CONFIG_FILE, "r") as f:
                config = json.load(f)
                expo_push_token = config.get("expo_push_token")
            
            if not expo_push_token:
                print("[FCM] No expo push token found")
                return False
            
            print("[FCM] Registering device for push notifications...")
            endpoint = "https://companion-rust.facepunch.com/api/push/register"
            payload = {
                "AuthToken": self.rustplus_token,
                "DeviceId": "rustplus-raid-alarms",
                "PushKind": 3,  # Expo
                "PushToken": expo_push_token,
            }
            
            resp = requests.post(
                endpoint, 
                headers={"Content-Type": "application/json"}, 
                json=payload, 
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # Update token if refreshed
                refreshed_token = data.get("token") or data.get("authToken")
                if refreshed_token:
                    self.rustplus_token = refreshed_token
                    with open(self.TOKEN_FILE, "w") as f:
                        json.dump({
                            "token": refreshed_token,
                            "steam_id": self.steam_id
                        }, f, indent=2)
                    print("[FCM] Refreshed Rust+ auth token saved")
                
                print("[FCM] Device registered for push notifications")
                return True
            else:
                print(f"[FCM] Push register failed: {resp.status_code} {resp.text}")
                return False
                
        except Exception as e:
            print(f"[FCM] Error registering device: {e}")
            return False

    def run(self):
        """Main thread loop for FCM listening"""
        if self.running:
            return
        
        self.running = True
        
        # Import rustplus dependencies
        try:
            global FCMListener, RustSocket, ServerDetails
            from rustplus import FCMListener, RustSocket, ServerDetails
        except ImportError as e:
            self.status_changed.emit("❌ rustplus library not installed", "#ff4444")
            print(f"[FCM] Import error: {e}")
            self.running = False
            return
        
        # Check authentication
        if not self.is_authenticated():
            self.status_changed.emit("❌ Not authenticated", "#ff4444")
            self.running = False
            return
        
        def dbg(msg):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [FCM service] {msg}")

        try:
            self.status_changed.emit("Starting FCM listener...", "#ffa500")
            dbg("Starting FCM listener (process mode)")
            
            # Start FCM listener in a separate process for reliable shutdown
            if self.fcm_credentials:
                self.fcm_listener_process = multiprocessing.Process(
                    target=fcm_listener_worker,
                    args=(self.fcm_credentials, self.notification_queue)
                )
                self.fcm_listener_process.start()
                dbg(f"FCM listener subprocess started (pid={self.fcm_listener_process.pid})")
                try:
                    self.running_changed.emit(True)
                except Exception:
                    pass
            else:
                raise RuntimeError("No FCM credentials available")

            self.status_changed.emit("✓ FCM listener active", "#00ff00")
            dbg("FCM listener started and waiting for notifications...")
            
            # Listen for notifications from the worker process
            while self.running:
                try:
                    # Check for notifications from worker (non-blocking)
                    if not self.notification_queue.empty():
                        obj, notification, data_message = self.notification_queue.get_nowait()
                        # Process notification in main service
                        self._on_notification(obj, notification, data_message)
                    else:
                        time.sleep(0.1)  # Short sleep to avoid busy waiting
                except Exception as e:
                    dbg(f"Error processing notification queue: {e}")
                    time.sleep(1)
            
        except Exception as e:
            error_msg = str(e)
            dbg(f"Error: {error_msg}")
            self.status_changed.emit(f"❌ Error: {error_msg[:50]}", "#ff4444")
        finally:
            self.running = False
            if self.fcm_listener_process:
                if self.fcm_listener_process.is_alive():
                    self.fcm_listener_process.terminate()
                    self.fcm_listener_process.join(timeout=2)
            try:
                self.running_changed.emit(False)
            except Exception:
                pass

    def _on_notification(self, obj, notification, data_message):
        """Handle incoming FCM notification"""
        try:
            def dbg(msg):
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [FCM service] {msg}")

            dbg("Notification Received")
            
            # Extract data from DataMessageStanza object
            data = {}
            if hasattr(data_message, 'data'):
                data = data_message.data if isinstance(data_message.data, dict) else {}
            elif hasattr(data_message, '__dict__'):
                data = {k: v for k, v in data_message.__dict__.items() if not k.startswith('_')}

            # Get notification ID to check if we've already seen this (TestAuthFlow logic)
            # Use persistent_id which is stable across deliveries
            notif_id = data.get("persistent_id") or data.get("id")
            
            # Parse notification data
            app_data_list = data.get("app_data", [])
            notification_type = None
            title = None
            message = None
            body_data = {}

            for app_data in app_data_list:
                if hasattr(app_data, 'key') and hasattr(app_data, 'value'):
                    key = app_data.key
                    value = app_data.value

                    # Extract common fields
                    if key == 'title' or key == 'gcm.notification.title':
                        title = value
                    elif key == 'message' or key == 'gcm.notification.body':
                        message = value
                    elif key == 'channelId':
                        notification_type = value
                    elif key == 'body':
                        try:
                            body_data = json.loads(value)
                        except (json.JSONDecodeError, AttributeError):
                            body_data = {'raw': value}
            
            # Display parsed notification (TestAuthFlow style)
            print(f"[FCM] Category: {data.get('category', 'N/A')}")
            print(f"[FCM] From: {data.get('from_', 'N/A')}")
            
            print("[FCM] --- Notification Details ---")
            if notification_type:
                print(f"[FCM] Type: {notification_type}")
            if title:
                print(f"[FCM] Title: {title}")
            if message:
                print(f"[FCM] Message: {message}")
            
            if body_data:
                print("[FCM] Body Data:")
                for key, value in body_data.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"[FCM]   {key}: {value[:100]}...")
                    else:
                        print(f"[FCM]   {key}: {value}")
            
            print("[FCM] ----------------------------")
            
            # Check for duplicates and save notification ID (TestAuthFlow logic)
            if notif_id in self.seen_notifications:
                print(f"[FCM] Ignoring already-seen notification: {notif_id}")
                return

            if notif_id:
                self.save_seen_notification(notif_id)
                print(f"[FCM] Notification ID: {notif_id} (saved)")
            
            # Handle server pairing notifications
            if notification_type == 'pairing' and body_data.get('type') == 'server':
                player_id = body_data.get("playerId")
                player_token = body_data.get("playerToken")
                
                if body_data.get('id') and body_data.get('ip') and body_data.get('port'):
                    print(f"[FCM] Server pairing detected: {body_data.get('name')}")
                    self.save_pairing(
                        body_data.get('id'),
                        body_data.get('name'),
                        body_data.get('ip'),
                        body_data.get('port'),
                        player_id,
                        player_token
                    )
                    self.status_changed.emit(
                        f"✓ Paired with {body_data.get('name')}",
                        "#00ff00"
                    )
                    return  # Don't process pairing notifications as regular notifications
            
            # Check if notification is from paired server (ID and IP/name fallback)
            notif_server_id = body_data.get('id') or body_data.get('server_id')
            notif_server_name = body_data.get('name') or body_data.get('server_name', 'Unknown')
            notif_server_ip = body_data.get('ip')
            notif_server_port = body_data.get('port')
            
            # Display notification details
            print(f"[FCM] Type: {notification_type}")
            if title:
                print(f"[FCM] Title: {title}")
            if message:
                print(f"[FCM] Message: {message}")
            if notif_server_name and notif_server_ip:
                print(f"[FCM] Server: {notif_server_name} ({notif_server_ip}:{notif_server_port})")
            
            if self.is_paired():
                id_mismatch = False
                ip_mismatch = False
                name_mismatch = False

                # Prefer ID check when available
                if notif_server_id and self.paired_server_id:
                    id_mismatch = (notif_server_id != self.paired_server_id)

                # Fallback IP:port check when ID absent or mismatch
                if self.paired_server_ip and notif_server_ip:
                    ip_mismatch = (str(self.paired_server_ip) != str(notif_server_ip) or str(self.paired_server_port) != str(notif_server_port))

                # Optional name check if provided by both sides
                if self.paired_server_name and notif_server_name:
                    name_mismatch = (str(self.paired_server_name).strip().lower() != str(notif_server_name).strip().lower())

                # Decide to ignore if clear mismatch on ID or on IP:port; name mismatch alone doesn't block
                if id_mismatch and ip_mismatch:
                    print(f"[FCM] Notification from different server (ID/IP mismatch), ignoring")
                    return
            
            # Only process alarm notifications (lowercase 'alarm')
            if notification_type and str(notification_type).lower() != 'alarm':
                # Ignore non-alarm notifications here
                return

            # Mandatory keyword filtering
            mandatory_keyword = (self.config.get("fcm_filter_keyword", "") or "").lower()
            if not mandatory_keyword:
                print("[FCM] Mandatory keyword not set - skipping notification")
                self.status_changed.emit("❌ Keyword required in Beta tab", "#ff4444")
                return

            # Check keyword in title/message/body
            text_parts = [title or '', message or '']
            # Include body_data string values for matching
            for kv in body_data.values():
                if isinstance(kv, str):
                    text_parts.append(kv)
            full_text = " ".join(text_parts).lower()
            if mandatory_keyword not in full_text:
                print(f"[FCM] Filtered out - keyword '{mandatory_keyword}' not found")
                return
            
            # Emit notification with server info
            notification_text = message or title or "Notification received"
            
            # Include server info in notification
            if notif_server_name and notif_server_ip:
                notification_with_server = f"[{notif_server_name} @ {notif_server_ip}:{notif_server_port}] {notification_text}"
            else:
                notification_with_server = notification_text
            
            self.notification_count += 1
            self.message_received.emit(notification_with_server)
            
            # Update status
            self.status_changed.emit(
                f"✓ FCM active ({self.notification_count} notifications)", 
                "#00ff00"
            )
            
            dbg(f"Notification forwarded to plugins: {notification_text}")
            
        except Exception as e:
            print(f"[FCM] Notification handler error: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self):
        """Stop the FCM listener subprocess"""
        def dbg(msg):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [FCM service] {msg}")

        dbg("Stopping FCM listener subprocess...")
        self.running = False
        if self.fcm_listener_process and self.fcm_listener_process.is_alive():
            pid = getattr(self.fcm_listener_process, 'pid', None)
            self.fcm_listener_process.terminate()
            self.fcm_listener_process.join(timeout=2)
            if self.fcm_listener_process.is_alive():
                print(f"[FCM] Subprocess did not exit; forcing kill (pid={pid})")
                try:
                    if os.name == 'nt' and pid:
                        subprocess.run(["taskkill", "/F", "/PID", str(pid), "/T"], check=False)
                    else:
                        # POSIX fallback
                        try:
                            os.killpg(os.getpgid(pid), 9)
                        except Exception:
                            os.kill(pid, 9)
                except Exception as kill_exc:
                    print(f"[FCM] Failed to force-kill subprocess: {kill_exc}")
            else:
                dbg("FCM listener subprocess terminated.")
            # Emit status update for UI
            try:
                self.status_changed.emit("● Offline", "#888888")
            except Exception:
                pass
            # Clear reference
            try:
                self.fcm_listener_process = None
            except Exception:
                pass
            try:
                self.running_changed.emit(False)
            except Exception:
                pass
        if self.isRunning():
            self.wait(2000)  # Wait up to 2 seconds for thread to finish
