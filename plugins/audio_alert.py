"""
Audio Alert Plugin - Play MP3 files on raid alerts

A simple single-file plugin that plays audio files through selected sound devices.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFrame, QFileDialog, QComboBox,
    QSpinBox, QMessageBox, QSlider, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from plugin_base import PluginBase
from pathlib import Path
import sys

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    if sys.platform == "win32":
        import sounddevice as sd
        SOUNDDEVICE_AVAILABLE = True
    else:
        SOUNDDEVICE_AVAILABLE = False
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class AudioPlaybackThread(QThread):
    """Thread for playing audio without blocking UI"""
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, file_path, device_id=None, volume=1.0):
        super().__init__()
        self.file_path = file_path
        self.device_id = device_id
        self.volume = volume
        self._stop_requested = False
    
    def run(self):
        try:
            # Initialize mixer if not already done
            if not pygame.mixer.get_init():
                if self.device_id and self.device_id != "Default":
                    pygame.mixer.init(devicename=self.device_id)
                else:
                    pygame.mixer.init()
            
            # Load and play
            pygame.mixer.music.load(self.file_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            
            # Wait for playback to finish or stop requested
            while pygame.mixer.music.get_busy() and not self._stop_requested:
                pygame.time.Clock().tick(10)
            
            if self._stop_requested:
                pygame.mixer.music.stop()
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Request thread to stop"""
        self._stop_requested = True


class Plugin(PluginBase):
    """Audio Alert Plugin"""
    
    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.widget = None
        self.playback_threads = []
        
        # Initialize pygame mixer
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except:
                pass
    
    def get_name(self):
        return "Audio Alert"
    
    def get_icon(self):
        return "🔊"
    
    def get_description(self):
        return "Play audio files on raid alerts through multiple devices"
    
    def get_widget(self):
        if self.widget is None:
            self.widget = self._build_ui()
        return self.widget
    
    def _build_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QFrame()
        header.setObjectName("heroCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("🔊 Audio Alert")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Play audio files on raid alerts through selected devices")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Warning if pygame not installed
        if not PYGAME_AVAILABLE:
            warning_frame = QFrame()
            warning_frame.setObjectName("card")
            warning_layout = QVBoxLayout(warning_frame)
            warning_layout.setContentsMargins(16, 16, 16, 16)
            
            warning = QLabel("⚠️ Pygame library not installed")
            warning.setFont(QFont("Segoe UI", 12, QFont.Bold))
            warning.setStyleSheet("color: #ff8800;")
            warning_layout.addWidget(warning)
            
            install_msg = QLabel("Install it with: pip install pygame")
            install_msg.setFont(QFont("Segoe UI", 10))
            install_msg.setStyleSheet("color: #b8b8b8;")
            warning_layout.addWidget(install_msg)
            
            layout.addWidget(warning_frame)
        
        # Warning if sounddevice not installed
        if not SOUNDDEVICE_AVAILABLE:
            warning_frame = QFrame()
            warning_frame.setObjectName("card")
            warning_layout = QVBoxLayout(warning_frame)
            warning_layout.setContentsMargins(16, 16, 16, 16)
            
            warning = QLabel("⚠️ Sounddevice library not installed (device detection disabled)")
            warning.setFont(QFont("Segoe UI", 11, QFont.Bold))
            warning.setStyleSheet("color: #ff8800;")
            warning_layout.addWidget(warning)
            
            install_msg = QLabel("Install it with: pip install sounddevice")
            install_msg.setFont(QFont("Segoe UI", 10))
            install_msg.setStyleSheet("color: #b8b8b8;")
            warning_layout.addWidget(install_msg)
            
            layout.addWidget(warning_frame)
        
        # Audio Devices Group
        if SOUNDDEVICE_AVAILABLE:
            devices_group = QGroupBox("Audio Output Devices")
            devices_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
            devices_group.setStyleSheet(self.get_groupbox_style())
            devices_layout = QVBoxLayout(devices_group)
            
            scan_btn = QPushButton("🔍 Scan Audio Devices")
            scan_btn.setMinimumHeight(36)
            scan_btn.setStyleSheet(self.get_button_style("#0e639c"))
            scan_btn.clicked.connect(lambda: self.scan_audio_devices(devices_layout))
            devices_layout.addWidget(scan_btn)
            
            # Scrollable container for device list
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setMinimumHeight(150)
            scroll_area.setMaximumHeight(300)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 1px solid #2a2c33;
                    border-radius: 8px;
                    background-color: #1e1e1e;
                }
            """)
            
            self.devices_container = QWidget()
            self.devices_container_layout = QVBoxLayout(self.devices_container)
            self.devices_container_layout.setContentsMargins(8, 8, 8, 8)
            self.devices_container_layout.setSpacing(6)
            self.devices_container_layout.addStretch()  # Push items to top
            
            scroll_area.setWidget(self.devices_container)
            devices_layout.addWidget(scroll_area)
            
            layout.addWidget(devices_group)
        
        # Audio Files Group
        self.audio_entries = []
        self.create_audio_entries(layout)
        
        # Add Audio Button
        add_btn = QPushButton("➕ Add Another Audio File")
        add_btn.setMinimumHeight(36)
        add_btn.setStyleSheet(self.get_button_style("#6c757d"))
        add_btn.clicked.connect(lambda: self.add_audio_entry(layout))
        layout.addWidget(add_btn)
        
        # Test All Button
        test_frame = QFrame()
        test_frame.setObjectName("card")
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(16, 16, 16, 16)
        
        test_btn = QPushButton("🔊 Test Play All")
        test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        test_btn.setMinimumHeight(48)
        test_btn.setStyleSheet(self.get_button_style("#0e639c"))
        test_btn.clicked.connect(self.test_play_all)
        test_layout.addWidget(test_btn)
        
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px;")
        test_layout.addWidget(self.status_label)
        
        layout.addWidget(test_frame)
        layout.addStretch()
        
        # Auto-scan devices after UI is built
        if SOUNDDEVICE_AVAILABLE:
            saved_devices = self.config.get("audio_alert_devices", [])
            if saved_devices:
                # Use QTimer to defer scan until after widget is shown
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.scan_audio_devices(None))
        
        return widget
    
    def create_audio_entries(self, parent_layout):
        """Create initial audio entries from config"""
        saved_audios = self.config.get("audio_alert_files", [])
        
        if not saved_audios:
            # Create one default entry
            self.add_audio_entry(parent_layout)
        else:
            for audio_data in saved_audios:
                self.add_audio_entry(parent_layout, audio_data)
    
    def add_audio_entry(self, parent_layout, audio_data=None):
        """Add a new audio file entry"""
        if audio_data is None:
            audio_data = {
                "file_path": "",
                "volume": 100
            }
        
        # Create group
        group = QGroupBox(f"Audio File #{len(self.audio_entries) + 1}")
        group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        group.setStyleSheet(self.get_groupbox_style())
        group_layout = QVBoxLayout(group)
        
        # File path row
        file_row = QHBoxLayout()
        file_label = QLabel("Audio File:")
        file_label.setMinimumWidth(100)
        file_label.setFont(QFont("Segoe UI", 10))
        file_row.addWidget(file_label)
        
        file_input = QLineEdit(audio_data.get("file_path", ""))
        file_input.setPlaceholderText("Path to MP3 file...")
        file_input.setMinimumHeight(32)
        file_input.textChanged.connect(self.save_audio_config)
        file_row.addWidget(file_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setMinimumHeight(32)
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(lambda: self.browse_file(file_input))
        file_row.addWidget(browse_btn)
        
        group_layout.addLayout(file_row)
        
        # Volume row
        volume_row = QHBoxLayout()
        volume_label = QLabel("Volume:")
        volume_label.setMinimumWidth(100)
        volume_label.setFont(QFont("Segoe UI", 10))
        volume_row.addWidget(volume_label)
        
        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(audio_data.get("volume", 100))
        volume_slider.setMinimumWidth(150)
        volume_slider.valueChanged.connect(self.save_audio_config)
        volume_row.addWidget(volume_slider)
        
        volume_spin = QSpinBox()
        volume_spin.setRange(0, 100)
        volume_spin.setValue(audio_data.get("volume", 100))
        volume_spin.setSuffix("%")
        volume_spin.setMinimumHeight(32)
        volume_spin.setMaximumWidth(80)
        volume_spin.valueChanged.connect(self.save_audio_config)
        volume_row.addWidget(volume_spin)
        
        # Sync slider and spinbox
        volume_slider.valueChanged.connect(volume_spin.setValue)
        volume_spin.valueChanged.connect(volume_slider.setValue)
        
        # Test button for this entry
        test_btn = QPushButton("▶ Test")
        test_btn.setMinimumHeight(32)
        test_btn.setMaximumWidth(100)
        test_btn.setStyleSheet(self.get_button_style("#0e639c"))
        test_btn.clicked.connect(
            lambda: self.test_play_single(file_input.text(), volume_spin.value())
        )
        volume_row.addWidget(test_btn)
        
        # Remove button
        remove_btn = QPushButton("🗑")
        remove_btn.setMinimumHeight(32)
        remove_btn.setMaximumWidth(50)
        remove_btn.setStyleSheet(self.get_button_style("#c50f1f"))
        remove_btn.clicked.connect(lambda: self.remove_audio_entry(group))
        volume_row.addWidget(remove_btn)
        
        volume_row.addStretch()
        group_layout.addLayout(volume_row)
        
        # Store references
        # Store references
        entry = {
            "group": group,
            "file_input": file_input,
            "volume_spin": volume_spin,
            "volume_slider": volume_slider
        }
        self.audio_entries.append(entry)
        
        # Insert before the "Add Another" button
        insert_index = parent_layout.count() - 3  # Before add button, test frame, and stretch
        parent_layout.insertWidget(insert_index, group)
    
    def remove_audio_entry(self, group):
        """Remove an audio entry"""
        for i, entry in enumerate(self.audio_entries):
            if entry["group"] == group:
                self.audio_entries.pop(i)
                group.deleteLater()
                self.save_audio_config()
                break
        
        # Renumber remaining groups
        for i, entry in enumerate(self.audio_entries):
            entry["group"].setTitle(f"Audio File #{i + 1}")
    
    def scan_audio_devices(self, parent_layout):
        """Scan and display available audio output devices"""
        if not SOUNDDEVICE_AVAILABLE:
            return
        
        # Clear previous devices
        while self.devices_container_layout.count():
            child = self.devices_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        try:
            devices = sd.query_devices()
            saved_devices = self.config.get("audio_alert_devices", [])
            
            output_devices = []
            for idx, device in enumerate(devices):
                # Only show output devices
                if device['max_output_channels'] > 0:
                    output_devices.append((idx, device['name']))
            
            if not output_devices:
                no_devices = QLabel("No output devices found")
                no_devices.setStyleSheet("color: #888888; padding: 10px;")
                self.devices_container_layout.addWidget(no_devices)
                return
            
            # Create checkboxes for each device
            self.device_checkboxes = []
            for idx, name in output_devices:
                checkbox = QCheckBox(f"{name} (ID: {idx})")
                checkbox.setFont(QFont("Segoe UI", 10))
                checkbox.setStyleSheet("padding: 4px;")
                
                # Check if device was previously selected
                if name in saved_devices:
                    checkbox.setChecked(True)
                
                checkbox.stateChanged.connect(self.save_selected_devices)
                self.device_checkboxes.append((name, checkbox))
                self.devices_container_layout.insertWidget(
                    self.devices_container_layout.count() - 1,  # Insert before stretch
                    checkbox
                )
            
            # Only update status if label exists
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"✓ Found {len(output_devices)} output device(s)")
                self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
            
        except Exception as e:
            error_label = QLabel(f"Error scanning devices: {str(e)[:50]}")
            error_label.setStyleSheet("color: #ff4444; padding: 10px;")
            self.devices_container_layout.addWidget(error_label)
    
    def save_selected_devices(self):
        """Save selected audio devices to config"""
        if not hasattr(self, 'device_checkboxes'):
            return
        
        selected = []
        for name, checkbox in self.device_checkboxes:
            if checkbox.isChecked():
                selected.append(name)
        
        self.config["audio_alert_devices"] = selected
    
    def browse_file(self, file_input):
        """Open file browser for audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.ogg);;All Files (*.*)"
        )
        if file_path:
            file_input.setText(file_path)
    
    def save_audio_config(self):
        """Save all audio entries to config"""
        audio_files = []
        for entry in self.audio_entries:
            audio_files.append({
                "file_path": entry["file_input"].text().strip(),
                "volume": entry["volume_spin"].value()
            })
        
        self.config["audio_alert_files"] = audio_files
    
    def test_play_single(self, file_path, volume):
        """Test play a single audio file on all selected devices"""
        if not PYGAME_AVAILABLE:
            QMessageBox.warning(None, "Pygame Not Installed", "Please install pygame:\n\npip install pygame")
            return
        
        if not file_path or not Path(file_path).exists():
            self.status_label.setText("❌ Audio file not found")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return
        
        self.status_label.setText(f"▶ Playing: {Path(file_path).name}")
        self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
        
        # Get selected devices or use default
        selected_devices = self.config.get("audio_alert_devices", [])
        if not selected_devices and SOUNDDEVICE_AVAILABLE:
            selected_devices = ["Default"]
        
        # Play on each selected device
        if SOUNDDEVICE_AVAILABLE and selected_devices:
            for device_name in selected_devices:
                thread = AudioPlaybackThread(file_path, device_name if device_name != "Default" else None, volume / 100.0)
                thread.finished.connect(lambda t=thread: self.on_playback_finished(t))
                thread.error.connect(self.on_playback_error)
                self.playback_threads.append(thread)
                thread.start()
        else:
            # Fallback to default device
            thread = AudioPlaybackThread(file_path, None, volume / 100.0)
            thread.finished.connect(lambda: self.on_playback_finished(thread))
            thread.error.connect(self.on_playback_error)
            self.playback_threads.append(thread)
            thread.start()
    
    def test_play_all(self):
        """Test play all configured audio files"""
        if not PYGAME_AVAILABLE:
            QMessageBox.warning(None, "Pygame Not Installed", "Please install pygame:\n\npip install pygame")
            return
        
        self.play_all_audio()
    
    def play_all_audio(self):
        """Play all configured audio files on selected devices"""
        audio_files = self.config.get("audio_alert_files", [])
        selected_devices = self.config.get("audio_alert_devices", [])
        
        if not audio_files:
            self.status_label.setText("❌ No audio files configured")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return
        
        # If no devices selected, play on default
        if not selected_devices and SOUNDDEVICE_AVAILABLE:
            selected_devices = ["Default"]
        
        valid_count = 0
        
        # Play each audio file on each selected device
        for audio_data in audio_files:
            file_path = audio_data.get("file_path", "")
            if file_path and Path(file_path).exists():
                volume = audio_data.get("volume", 100)
                
                # If sounddevice is available and devices are selected, use them
                if SOUNDDEVICE_AVAILABLE and selected_devices:
                    for device_name in selected_devices:
                        # Create playback thread for each device
                        thread = AudioPlaybackThread(
                            file_path,
                            device_name if device_name != "Default" else None,
                            volume / 100.0
                        )
                        thread.finished.connect(lambda t=thread: self.on_playback_finished(t))
                        thread.error.connect(self.on_playback_error)
                        self.playback_threads.append(thread)
                        thread.start()
                        valid_count += 1
                else:
                    # Fallback to default device
                    thread = AudioPlaybackThread(
                        file_path,
                        None,
                        volume / 100.0
                    )
                    thread.finished.connect(lambda t=thread: self.on_playback_finished(t))
                    thread.error.connect(self.on_playback_error)
                    self.playback_threads.append(thread)
                    thread.start()
                    valid_count += 1
        
        if valid_count > 0:
            self.status_label.setText(f"🔊 Playing {valid_count} audio stream(s)...")
            self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
        else:
            self.status_label.setText("❌ No valid audio files found")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
    
    def on_playback_finished(self, thread):
        """Handle playback completion"""
        if thread in self.playback_threads:
            self.playback_threads.remove(thread)
        
        # Wait for thread to fully finish
        if thread.isRunning():
            thread.wait(1000)
        
        if not self.playback_threads:
            self.status_label.setText("✓ Playback finished")
            self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
    
    def on_playback_error(self, error_msg):
        """Handle playback error"""
        self.status_label.setText(f"❌ Error: {error_msg[:50]}")
        self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
        print(f"[AudioAlert] Playback error: {error_msg}")
    
    def on_telegram_message(self, message: str):
        """Called when Telegram message received - play all audio"""
        print("[AudioAlert] Raid alert received, playing audio...")
        self.play_all_audio()
    
    def cleanup(self):
        """Stop all playback threads when plugin is unloaded"""
        for thread in self.playback_threads[:]:  # Copy list to avoid modification during iteration
            if thread.isRunning():
                thread.stop()
                thread.wait(2000)  # Wait up to 2 seconds for thread to finish
        self.playback_threads.clear()
    
    def get_groupbox_style(self):
        return """
            QGroupBox {
                background-color: #131418;
                border: 1px solid #2a2c33;
                border-radius: 14px;
                padding: 18px 12px 12px 12px;
                margin-top: 12px;
                color: #d4d4d4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 6px 10px;
                color: #d4d4d4;
                font-weight: 600;
            }
        """
    
    def get_button_style(self, bg_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_color}dd;
            }}
            QPushButton:pressed {{
                background-color: {bg_color}aa;
            }}
        """
