"""
Telegram Service - Shared service for monitoring Telegram messages
"""

import asyncio
import time
from PySide6.QtCore import QThread, Signal
from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest


class TelegramService(QThread):
    """
    Shared Telegram service that monitors for new messages
    Emits signals that plugins can connect to
    """
    
    message_received = Signal(str)  # Emitted when new message arrives
    status_changed = Signal(str, str)  # status text, color
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = False
        self.bot = None
        self.loop = None
    
    def run(self):
        """Main thread loop for Telegram polling"""
        if self.running:
            return
        
        self.running = True
        self.status_changed.emit("Connecting to Telegram...", "#ffa500")
        
        bot_token = self.config.get("telegram_bot_token", "")
        chat_id = self.config.get("telegram_chat_id", "")
        
        # Validate credentials
        if not bot_token or not chat_id:
            self.status_changed.emit("❌ Bot token or chat ID not configured", "#ff4444")
            self.running = False
            return
        
        if ":" not in bot_token:
            self.status_changed.emit("❌ Invalid bot token format", "#ff4444")
            self.running = False
            return
        
        # Create event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            # Initialize bot with longer timeouts for slow connections
            request = HTTPXRequest(
                connection_pool_size=1,
                connect_timeout=60,
                read_timeout=60,
                pool_timeout=60
            )
            self.bot = Bot(token=bot_token, request=request)
            
            # Test connection with extended timeout
            print(f"[Telegram] Testing connection with bot token: {bot_token[:10]}...")
            bot_info = self.loop.run_until_complete(
                asyncio.wait_for(self.bot.get_me(), timeout=60.0)
            )
            
            self.status_changed.emit(
                f"✓ Connected as @{bot_info.username}", 
                "#00ff00"
            )
            print(f"[Telegram] Connected as @{bot_info.username}")
            
            # Start polling
            self.poll_messages(chat_id)
            
        except asyncio.TimeoutError:
            print("[Telegram] Connection timeout - check network/firewall")
            self.status_changed.emit("❌ Connection timeout - retrying in 10s...", "#ff4444")
            self.retry_connection(10)
        except TelegramError as e:
            error_msg = str(e)
            print(f"[Telegram] TelegramError: {error_msg}")
            if "Unauthorized" in error_msg:
                self.status_changed.emit("❌ Invalid bot token", "#ff4444")
            elif "Not Found" in error_msg:
                self.status_changed.emit("❌ Bot not found", "#ff4444")
            else:
                self.status_changed.emit(f"❌ Telegram error: {error_msg[:50]} - retrying in 10s...", "#ff4444")
                self.retry_connection(10)
        except Exception as e:
            error_msg = str(e)
            print(f"[Telegram] Exception: {error_msg}")
            self.status_changed.emit(f"❌ Error: {error_msg[:50]} - retrying in 10s...", "#ff4444")
            self.retry_connection(10)
        finally:
            # Cleanup event loop
            if self.loop:
                try:
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    # Run the loop one more time to process cancellations
                    if pending:
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception as e:
                    print(f"[Telegram] Error during loop cleanup: {e}")
                finally:
                    self.loop.close()
            self.running = False
    
    def poll_messages(self, chat_id):
        """Poll for new messages"""
        last_update_id = 0
        first_run = True  # Flag to skip initial old messages
        
        while self.running:
            try:
                # Get updates
                updates = self.loop.run_until_complete(
                    asyncio.wait_for(
                        self.bot.get_updates(
                            timeout=5,
                            offset=last_update_id + 1 if last_update_id > 0 else None
                        ),
                        timeout=10.0
                    )
                )
                
                # On first run, just mark all existing messages as seen
                if first_run and updates:
                    print(f"[Telegram] First run - marking {len(updates)} existing messages as seen")
                    for update in updates:
                        last_update_id = update.update_id
                        
                        # Update last_message_id to skip old messages
                        if update.message and str(update.message.chat_id) == str(chat_id):
                            self.config["last_message_id"] = update.message.message_id
                        elif update.channel_post and str(update.channel_post.chat_id) == str(chat_id):
                            self.config["last_message_id"] = update.channel_post.message_id
                    
                    first_run = False
                    print("[Telegram] Ready - will only process new messages from now on")
                    continue
                
                first_run = False  # Set to False after first iteration
                
                # Process updates normally
                for update in updates:
                    last_update_id = update.update_id
                    
                    # Handle regular messages
                    if update.message:
                        if str(update.message.chat_id) == str(chat_id):
                            message_id = update.message.message_id
                            message_text = update.message.text or ""
                            
                            if message_id > self.config.get("last_message_id", 0):
                                if self._passes_filter(message_text):
                                    self.config["last_message_id"] = message_id
                                    self.message_received.emit(message_text)
                    
                    # Handle channel posts
                    elif update.channel_post:
                        if str(update.channel_post.chat_id) == str(chat_id):
                            post_id = update.channel_post.message_id
                            post_text = update.channel_post.text or ""
                            
                            if post_id > self.config.get("last_message_id", 0):
                                if self._passes_filter(post_text):
                                    self.config["last_message_id"] = post_id
                                    self.message_received.emit(post_text)
            
            except asyncio.TimeoutError:
                # Normal timeout, continue
                pass
            except TelegramError as e:
                error_msg = str(e)
                print(f"[Telegram] Polling TelegramError: {error_msg}")
                
                # Connection issues - try to restart
                if "Connection" in error_msg or "Network" in error_msg or "Timeout" in error_msg:
                    self.status_changed.emit(f"⚠ Connection lost: {error_msg[:40]} - restarting...", "#ffaa00")
                    print("[Telegram] Connection lost, attempting restart...")
                    self.restart_service()
                    return
                else:
                    self.status_changed.emit(f"⚠ Polling error: {error_msg[:30]}", "#ffaa00")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"[Telegram] Polling Exception: {error_msg}")
                
                # Check for connection-related errors
                if any(keyword in error_msg.lower() for keyword in ["connection", "network", "timeout", "unreachable", "failed to connect"]):
                    self.status_changed.emit(f"⚠ Connection lost: {error_msg[:40]} - restarting...", "#ffaa00")
                    print("[Telegram] Connection lost, attempting restart...")
                    self.restart_service()
                    return
                else:
                    self.status_changed.emit(f"⚠ Polling error: {error_msg[:30]}", "#ffaa00")
            
            # Interruptible sleep; respect live polling rate changes
            polling_rate = self.config.get("polling_rate", 2)
            for _ in range(polling_rate * 10):
                if not self.running:
                    break
                time.sleep(0.1)
    
    def stop(self):
        """Stop the Telegram service"""
        print("[Telegram] Stopping service...")
        self.running = False
        
        # Close the event loop if it exists
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self.isRunning():
            self.quit()
            self.wait(5000)  # Wait up to 5 seconds for thread to finish
        
        self.status_changed.emit("⏸ Stopped", "#888888")
    
    def restart_service(self):
        """Restart the Telegram service after connection loss"""
        print("[Telegram] Restarting service...")
        self.running = False
        
        # Cleanup current loop
        if self.loop:
            try:
                if self.loop.is_running():
                    self.loop.call_soon_threadsafe(self.loop.stop)
                
                # Cancel pending tasks
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                
                if not self.loop.is_closed():
                    self.loop.close()
            except Exception as e:
                print(f"[Telegram] Error during restart cleanup: {e}")
        
        self.loop = None
        
        # Wait a bit before restarting
        time.sleep(3)
        
        # Restart by calling run in a new thread
        if not self.isRunning():
            print("[Telegram] Starting new connection thread...")
            self.start()
        else:
            print("[Telegram] Thread still running, waiting for it to stop...")
            self.quit()
            self.wait(5000)
            if not self.isRunning():
                print("[Telegram] Thread stopped, starting new connection...")
                self.start()
    
    def retry_connection(self, delay_seconds):
        """Retry connection after a delay"""
        if not self.running:
            return
        
        print(f"[Telegram] Retrying connection in {delay_seconds} seconds...")
        time.sleep(delay_seconds)
        
        # Restart the service if still running
        if self.running:
            print("[Telegram] Attempting reconnection...")
            self.run()
    
    def is_running(self):
        """Check if service is running"""
        return self.running

    def _passes_filter(self, text: str) -> bool:
        """Return True if filter is disabled or keyword is matched"""
        enabled = bool(self.config.get("filter_enabled", False))
        keyword = (self.config.get("filter_keyword") or "").strip().lower()

        if not enabled:
            return True
        if not keyword:
            return True

        return keyword in (text or "").lower()
