"""
Relay Server - Broadcasts Telegram messages to multiple clients
Allows one person to run Telegram bot, others connect as clients
"""

import socket
import threading
import json
import hashlib
from PySide6.QtCore import QObject, Signal


class RelayServer(QObject):
    """Server that relays messages to connected clients"""
    
    status_changed = Signal(str, str)  # status text, color
    tunnel_url_ready = Signal(str)  # public URL from ngrok
    
    def __init__(self, port=5555, password=None):
        super().__init__()
        self.port = port
        self.password_hash = self._hash_password(password) if password else None
        self.server_socket = None
        self.clients = []
        self.running = False
        self.server_thread = None
        self.ngrok_process = None
        self.public_url = None
    
    def _hash_password(self, password):
        """Hash password using SHA256"""
        if not password:
            return None
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def set_password(self, password):
        """Set or update server password"""
        self.password_hash = self._hash_password(password) if password else None
        
    def start(self):
        """Start the relay server"""
        if self.running:
            return
            
        self.running = True
        self.clients = []
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Allow checking running flag
            
            # Start accepting connections in thread
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            
            self.status_changed.emit(f"✓ Server running on port {self.port}", "#00ff00")
            print(f"[Relay Server] Started on port {self.port}")
            
            # Start ngrok tunnel
            self._start_ngrok()
            
        except Exception as e:
            self.running = False
            self.status_changed.emit(f"❌ Failed to start server: {str(e)}", "#ff4444")
            print(f"[Relay Server] Error: {e}")
    
    def _start_ngrok(self):
        """Start ngrok tunnel for public access"""
        try:
            from pyngrok import ngrok, conf
            
            # Kill any existing ngrok processes
            try:
                ngrok.kill()
            except:
                pass
            
            # Start tunnel
            print(f"[Relay Server] Starting ngrok tunnel on port {self.port}...")
            tunnel = ngrok.connect(self.port, "tcp")
            self.public_url = tunnel.public_url
            
            # Extract host:port from tcp://X.tcp.ngrok.io:XXXXX
            if self.public_url.startswith("tcp://"):
                self.public_url = self.public_url[6:]  # Remove tcp://
            
            self.tunnel_url_ready.emit(self.public_url)
            self.status_changed.emit(f"✓ Public URL: {self.public_url}", "#00ff00")
            print(f"[Relay Server] Ngrok tunnel: {self.public_url}")
            
        except ImportError:
            msg = "⚠ ngrok not installed - server running locally only"
            self.status_changed.emit(msg, "#ffaa00")
            print("[Relay Server] pyngrok not installed. Install with: pip install pyngrok")
            print("[Relay Server] Server accessible on local network only")
        except Exception as e:
            error_msg = str(e)
            
            # Check for authentication error
            if "authentication failed" in error_msg or "ERR_NGROK_4018" in error_msg:
                msg = "⚠ ngrok auth required - server running locally only"
                self.status_changed.emit(msg, "#ffaa00")
                print("[Relay Server] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("[Relay Server] ⚠️  NGROK AUTHENTICATION REQUIRED")
                print("[Relay Server] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("[Relay Server] ")
                print("[Relay Server] To enable public access to your relay server:")
                print("[Relay Server] ")
                print("[Relay Server] 1. Sign up for free at: https://dashboard.ngrok.com/signup")
                print("[Relay Server] 2. Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken")
                print("[Relay Server] 3. Run: ngrok config add-authtoken YOUR_TOKEN_HERE")
                print("[Relay Server] ")
                print("[Relay Server] Without ngrok, your server only works on local network.")
                print("[Relay Server] Clan members must be on same WiFi/LAN to connect.")
                print("[Relay Server] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            else:
                msg = f"⚠ Tunnel error - server running locally only"
                self.status_changed.emit(msg, "#ffaa00")
                print(f"[Relay Server] Ngrok error: {error_msg[:100]}")
                print("[Relay Server] Server accessible on local network only")
    
    def _accept_connections(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[Relay Server] Client attempting to connect: {address}")
                
                # Handle authentication if password is set
                if self.password_hash:
                    if not self._authenticate_client(client_socket):
                        print(f"[Relay Server] Authentication failed for {address}")
                        client_socket.close()
                        continue
                
                # Add to clients list
                client_info = {
                    'socket': client_socket,
                    'address': address
                }
                self.clients.append(client_info)
                
                print(f"[Relay Server] Client authenticated: {address}")
                self.status_changed.emit(f"✓ {len(self.clients)} client(s) connected", "#00ff00")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[Relay Server] Accept error: {e}")
    
    def _authenticate_client(self, client_socket):
        """Authenticate client with password challenge"""
        try:
            # Send auth challenge
            challenge = json.dumps({'type': 'auth_required'}).encode('utf-8')
            challenge_length = len(challenge).to_bytes(4, 'big')
            client_socket.sendall(challenge_length + challenge)
            
            # Receive password response (with timeout)
            client_socket.settimeout(10.0)
            length_data = self._recv_exact(client_socket, 4)
            if not length_data:
                return False
            
            packet_length = int.from_bytes(length_data, 'big')
            packet_data = self._recv_exact(client_socket, packet_length)
            if not packet_data:
                return False
            
            # Parse response
            response = json.loads(packet_data.decode('utf-8'))
            if response.get('type') != 'auth_response':
                return False
            
            # Verify password hash
            client_password_hash = response.get('password_hash')
            if client_password_hash == self.password_hash:
                # Send success
                success = json.dumps({'type': 'auth_success'}).encode('utf-8')
                success_length = len(success).to_bytes(4, 'big')
                client_socket.sendall(success_length + success)
                client_socket.settimeout(None)
                return True
            else:
                # Send failure
                failure = json.dumps({'type': 'auth_failed'}).encode('utf-8')
                failure_length = len(failure).to_bytes(4, 'big')
                client_socket.sendall(failure_length + failure)
                return False
                
        except Exception as e:
            print(f"[Relay Server] Auth error: {e}")
            return False
    
    def _recv_exact(self, sock, n):
        """Receive exactly n bytes from socket"""
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
    
    def broadcast_message(self, message: str):
        """Broadcast message to all connected clients"""
        if not self.running:
            return
        
        # Create message packet
        packet = json.dumps({
            'type': 'message',
            'content': message
        }).encode('utf-8')
        packet_length = len(packet).to_bytes(4, 'big')
        
        # Send to all clients
        disconnected = []
        for client in self.clients:
            try:
                client['socket'].sendall(packet_length + packet)
            except Exception as e:
                print(f"[Relay Server] Failed to send to {client['address']}: {e}")
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.clients.remove(client)
            try:
                client['socket'].close()
            except:
                pass
        
        if disconnected:
            self.status_changed.emit(f"✓ {len(self.clients)} client(s) connected", "#00ff00")
    
    def stop(self):
        """Stop the relay server"""
        print("[Relay Server] Stopping...")
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client['socket'].close()
            except:
                pass
        self.clients = []
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Stop ngrok
        if self.ngrok_process:
            try:
                from pyngrok import ngrok
                ngrok.kill()
            except:
                pass
        
        # Wait for thread
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)
        
        self.status_changed.emit("⏸ Server stopped", "#888888")
        print("[Relay Server] Stopped")
    
    def get_connection_info(self):
        """Get connection info for clients"""
        local_ip = self._get_local_ip()
        
        info = {
            'local': f"{local_ip}:{self.port}",
            'public': self.public_url if self.public_url else None
        }
        
        return info
    
    def _get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


class RelayClient(QObject):
    """Client that connects to relay server"""
    
    message_received = Signal(str)
    status_changed = Signal(str, str)
    
    def __init__(self, server_address, password=None):
        super().__init__()
        self.server_address = server_address  # "host:port"
        self.password = password
        self.socket = None
        self.running = False
        self.receive_thread = None
    
    def _hash_password(self, password):
        """Hash password using SHA256"""
        if not password:
            return None
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def connect(self):
        """Connect to relay server"""
        if self.running:
            return
        
        try:
            # Parse address
            if ':' in self.server_address:
                host, port = self.server_address.rsplit(':', 1)
                port = int(port)
            else:
                self.status_changed.emit("❌ Invalid server address format", "#ff4444")
                return
            
            # Connect
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            
            self.status_changed.emit(f"Connecting to {host}:{port}...", "#ffa500")
            print(f"[Relay Client] Connecting to {host}:{port}...")
            
            self.socket.connect((host, port))
            
            # Handle authentication if server requires it
            if not self._handle_auth():
                self.running = False
                self.socket.close()
                self.status_changed.emit("❌ Authentication failed", "#ff4444")
                print("[Relay Client] Authentication failed")
                return
            
            self.running = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            self.status_changed.emit(f"✓ Connected to relay server", "#00ff00")
            print(f"[Relay Client] Connected to {host}:{port}")
            
        except Exception as e:
            self.running = False
            self.status_changed.emit(f"❌ Connection failed: {str(e)}", "#ff4444")
            print(f"[Relay Client] Error: {e}")
    
    def _handle_auth(self):
        """Handle authentication handshake with server"""
        try:
            # Read first message to see if auth is required
            self.socket.settimeout(10)
            length_data = self._recv_exact(4)
            if not length_data:
                return True  # No auth required
            
            packet_length = int.from_bytes(length_data, 'big')
            packet_data = self._recv_exact(packet_length)
            if not packet_data:
                return False
            
            packet = json.loads(packet_data.decode('utf-8'))
            
            # Check if auth is required
            if packet.get('type') == 'auth_required':
                if not self.password:
                    print("[Relay Client] Server requires password but none provided")
                    return False
                
                # Send password hash
                password_hash = self._hash_password(self.password)
                auth_response = json.dumps({
                    'type': 'auth_response',
                    'password_hash': password_hash
                }).encode('utf-8')
                auth_length = len(auth_response).to_bytes(4, 'big')
                self.socket.sendall(auth_length + auth_response)
                
                # Wait for auth result
                result_length = self._recv_exact(4)
                if not result_length:
                    return False
                
                result_packet_length = int.from_bytes(result_length, 'big')
                result_data = self._recv_exact(result_packet_length)
                if not result_data:
                    return False
                
                result = json.loads(result_data.decode('utf-8'))
                
                if result.get('type') == 'auth_success':
                    print("[Relay Client] Authentication successful")
                    self.socket.settimeout(None)
                    return True
                else:
                    print("[Relay Client] Authentication rejected")
                    return False
            else:
                # Not an auth message, server doesn't require auth
                # We need to put this message back somehow - or just assume no auth
                print("[Relay Client] Server does not require authentication")
                self.socket.settimeout(None)
                return True
                
        except Exception as e:
            print(f"[Relay Client] Auth error: {e}")
            return False
    
    def _receive_messages(self):
        """Receive messages from server"""
        while self.running:
            try:
                # Read packet length (4 bytes)
                length_data = self._recv_exact(4)
                if not length_data:
                    break
                
                packet_length = int.from_bytes(length_data, 'big')
                
                # Read packet data
                packet_data = self._recv_exact(packet_length)
                if not packet_data:
                    break
                
                # Parse packet
                packet = json.loads(packet_data.decode('utf-8'))
                
                if packet['type'] == 'message':
                    self.message_received.emit(packet['content'])
                    
            except Exception as e:
                if self.running:
                    print(f"[Relay Client] Receive error: {e}")
                    self.status_changed.emit(f"❌ Connection lost", "#ff4444")
                break
        
        self.running = False
    
    def _recv_exact(self, n):
        """Receive exactly n bytes"""
        data = b''
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
    
    def disconnect(self):
        """Disconnect from server"""
        print("[Relay Client] Disconnecting...")
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2)
        
        self.status_changed.emit("⏸ Disconnected", "#888888")
        print("[Relay Client] Disconnected")
    
    def is_connected(self):
        """Check if connected"""
        return self.running
