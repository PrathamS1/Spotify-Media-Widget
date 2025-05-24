import sys
import psutil
import win32gui
import win32process
import win32con
import win32api
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QHBoxLayout, QSlider, QFrame,
                            QSizePolicy, QToolTip, QGraphicsDropShadowEffect, QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize, QSettings
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPainterPath, QLinearGradient, QIcon, QPixmap
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
import logging
from datetime import datetime
import winreg
import warnings
import time
import win32com.client
import base64
import hashlib
import secrets
import requests
from urllib.parse import urlencode
import keyboard
from hotkey_settings_dialog import HotkeySettingsDialog
from hotkey_manager import HotkeyManager

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Setup logging to AppData directory
appdata_path = os.path.join(os.environ['APPDATA'], 'MediaWidget')
os.makedirs(appdata_path, exist_ok=True)
log_file = os.path.join(appdata_path, 'media_widget.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FadeLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opacity = 1.0
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def setText(self, text):
        if self.text() != text:
            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.0)
            self.animation.finished.connect(lambda: self._setTextAndFadeIn(text))
            self.animation.start()

    def _setTextAndFadeIn(self, text):
        super().setText(text)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.finished.disconnect()
        self.animation.start()

class ModernButton(QPushButton):
    def __init__(self, icon_path, parent=None, size=45):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(size, size)
        self.setIconSize(QSize(size-10, size-10))
        self.animation = QPropertyAnimation(self, b"iconSize")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutBack)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        self.setStyleSheet("""
            ModernButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
            }
            ModernButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            ModernButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
            ModernButton:disabled {
                opacity: 0.5;
            }
        """)

    def setIcon(self, icon):
        if self.icon() and self.icon().pixmap(32, 32).toImage() != icon.pixmap(32, 32).toImage():
            current_size = self.iconSize()
            self.animation.setStartValue(current_size)
            self.animation.setEndValue(QSize(current_size.width() + 5, current_size.height() + 5))
            self.animation.finished.connect(lambda: self._resetIconSize(icon))
            self.animation.start()
        super().setIcon(icon)

    def _resetIconSize(self, icon):
        super().setIcon(icon)
        current_size = self.iconSize()
        self.animation.setStartValue(current_size)
        self.animation.setEndValue(QSize(current_size.width() - 5, current_size.height() - 5))
        self.animation.finished.disconnect()
        self.animation.start()

class CloseButton(ModernButton):
    def __init__(self, parent=None):
        super().__init__(None, parent, size=25)
        self.setText("×")
        self.setStyleSheet("""
            CloseButton {
                background-color: transparent;
                color: #888888;
                border-radius: 12px;
                font-size: 30px;
                font-weight: bold;
            }
            CloseButton:hover {
                background-color: #ff4444;
                color: white;
            }
        """)

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            GlassFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)

class MediaWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Controller")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Initialize state
        self.is_spotify_running = False
        self.is_spotify_connected = False
        self.current_playback_state = None
        self.last_track_info = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_reconnect)
        
        # Create UI elements first
        self._create_ui()
        
        # Load settings after UI is created
        self.settings = QSettings('MediaWidget', 'SpotifyController')
        self.load_settings()
        
        # Initialize Spotify client
        self.spotify = None
        self.initialize_spotify()
        
        # Setup timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_media_players)
        self.timer.start(2000)  # Check every 2 seconds when active
        
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.check_idle_state)
        self.idle_timer.start(5000)  # Check idle state every 5 seconds
        
        # Connect button signals
        self.prev_button.clicked.connect(self.previous_track)
        self.play_button.clicked.connect(self.toggle_playback)
        self.next_button.clicked.connect(self.next_track)
        
        # For window dragging
        self.oldPos = None
        self.drag_start_pos = None
        
        # Update button states
        self.update_button_states()
        
        # Set startup with Windows
        self.set_startup_with_windows()
        
        # Initialize hotkey manager
        self.hotkey_manager = HotkeyManager(self)
        self._connect_hotkey_signals()
        self.hotkey_manager.start()

    def _create_ui(self):
        """Create and setup all UI elements"""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Add shadow effect with improved parameters
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 2)
        central_widget.setGraphicsEffect(shadow)
        
        # Create main content frame with improved styling
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 0.3);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Create header with close button and account menu inside content frame
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # Add account menu button with larger size
        self.account_button = QPushButton()
        self.account_button.setIcon(QIcon("icons/account.png"))
        self.account_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 8px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.account_button.setFixedSize(40, 40)
        self.account_button.setIconSize(QSize(24, 24))
        self.account_button.setCursor(Qt.PointingHandCursor)
        self.account_button.clicked.connect(self.show_account_menu)
        header_layout.addWidget(self.account_button)
        
        # Add settings button
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon("icons/settings.png"))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 8px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setIconSize(QSize(24, 24))
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.show_hotkey_settings)
        header_layout.addWidget(self.settings_button)
        
        # Add spacer
        header_layout.addStretch()
        
        # Make close button larger
        self.close_button = CloseButton()
        self.close_button.setFixedSize(40, 40)
        self.close_button.setIconSize(QSize(24, 24))
        self.close_button.clicked.connect(self.close)
        header_layout.addWidget(self.close_button, alignment=Qt.AlignRight)
        
        # Add header to content layout
        content_layout.addWidget(header_container)
        
        # Create UI elements with improved styling
        self.status_label = FadeLabel("No media player detected")
        self.status_label.setFont(QFont('Segoe UI', 9))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                background-color: transparent;
                border: none;
            }
        """)
        
        # Song info container with auto-height
        song_container = QWidget()
        song_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        song_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        song_layout = QVBoxLayout(song_container)
        song_layout.setContentsMargins(0, 0, 0, 0)
        song_layout.setSpacing(8)
        
        self.song_label = FadeLabel("")
        self.song_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        self.song_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: transparent;
                border: none;
            }
        """)
        self.song_label.setWordWrap(True)
        self.song_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.song_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.artist_label = FadeLabel("")
        self.artist_label.setFont(QFont('Segoe UI', 12))
        self.artist_label.setStyleSheet("""
            QLabel {
                color: #BBBBBB;
                background-color: transparent;
                border: none;
            }
        """)
        self.artist_label.setWordWrap(True)
        self.artist_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.artist_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        song_layout.addWidget(self.song_label)
        song_layout.addWidget(self.artist_label)
        
        # Volume slider with modern styling
        volume_container = QWidget()
        volume_layout = QHBoxLayout(volume_container)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(10)
        
        volume_icon = QLabel("🔊")
        volume_icon.setFont(QFont('Segoe UI', 12))
        volume_icon.setStyleSheet("color: #888888;")
        volume_icon.setFixedWidth(30)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: rgba(255, 255, 255, 0.1);
                margin: 2px 0;
                border-radius: 2px;
                opacity: 0.5;
            }
            QSlider::handle:horizontal {
                background: rgba(255, 255, 255, 0.5);
                border: none;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
                opacity: 0.5;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(0, 122, 255, 0.5);
                width: 14px;
                height: 14px;
                margin: -5px 0;
                opacity: 0.7;
            }
            QSlider::sub-page:horizontal {
                background: rgba(0, 122, 255, 0.2);
                border-radius: 2px;
                opacity: 0.5;
            }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        
        # Control buttons with glassmorphism background
        button_container = GlassFrame()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(15, 15, 15, 15)
        button_layout.setSpacing(25)
        button_layout.setAlignment(Qt.AlignCenter)
        
        self.prev_button = ModernButton("icons/prev.png")
        self.play_button = ModernButton("icons/play.png")
        self.next_button = ModernButton("icons/next.png")
        
        for button in [self.prev_button, self.play_button, self.next_button]:
            button_layout.addWidget(button)
        
        # Add widgets to content layout
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(song_container)
        content_layout.addWidget(volume_container)
        content_layout.addWidget(button_container)
        
        # Add content frame to main layout
        main_layout.addWidget(content_frame)
        
        # Set window size and position
        self.setMinimumWidth(360)
        self.setMaximumWidth(500)

    def load_settings(self):
        """Load saved settings"""
        pos = self.settings.value('position', QPoint(100, 100))
        self.move(pos)
        volume = self.settings.value('volume', 50, type=int)
        self.volume_slider.setValue(volume)

    def save_settings(self):
        """Save current settings"""
        self.settings.setValue('position', self.pos())
        self.settings.setValue('volume', self.volume_slider.value())

    def set_startup_with_windows(self):
        """Set the application to start with Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run",
                                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "MediaWidget", 0, winreg.REG_SZ, 
                            sys.executable + " " + os.path.abspath(__file__))
            winreg.CloseKey(key)
            logging.info("Added to Windows startup")
        except Exception as e:
            logging.error(f"Failed to set startup with Windows: {str(e)}")

    def check_idle_state(self):
        """Check if Spotify is idle and adjust refresh rate"""
        if not self.is_spotify_running or not self.current_playback_state:
            self.timer.setInterval(5000)  # Check every 5 seconds when idle
        else:
            self.timer.setInterval(2000)  # Check every 2 seconds when active

    def try_reconnect(self):
        """Attempt to reconnect to Spotify"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logging.info(f"Attempting to reconnect to Spotify (Attempt {self.reconnect_attempts})")
            self.initialize_spotify()
        else:
            self.reconnect_timer.stop()
            self.reconnect_attempts = 0
            logging.error("Max reconnection attempts reached")
            self.show_tooltip("Failed to connect to Spotify. Please check your connection.")

    def show_tooltip(self, message, duration=2000):
        """Show a tooltip message"""
        QToolTip.showText(self.mapToGlobal(self.rect().center()), message, self, self.rect(), duration)

    def update_button_states(self):
        """Update button states based on Spotify status"""
        is_enabled = self.is_spotify_running and self.is_spotify_connected
        self.prev_button.setEnabled(is_enabled)
        self.play_button.setEnabled(is_enabled)
        self.next_button.setEnabled(is_enabled)
        
        # Update account button icon based on connection state
        if self.is_spotify_connected:
            self.account_button.setIcon(QIcon("icons/account_connected.png"))
        else:
            self.account_button.setIcon(QIcon("icons/account.png"))

    def generate_code_verifier(self):
        """Generate a code verifier for PKCE"""
        code_verifier = secrets.token_urlsafe(32)
        return code_verifier

    def generate_code_challenge(self, code_verifier):
        """Generate a code challenge from the verifier"""
        sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')
        return code_challenge

    def initialize_spotify(self):
        """Initialize Spotify client with PKCE"""
        try:
            # Read client ID from file
            if not os.path.exists('spotify_credentials.json'):
                logging.error("Spotify credentials file not found")
                self.show_spotify_login()
                return

            with open('spotify_credentials.json', 'r') as f:
                credentials = json.load(f)

            if 'client_id' not in credentials:
                logging.error("Client ID not found in credentials file")
                self.show_spotify_login()
                return

            # Try to load existing token
            cache_path = os.path.join(os.environ['APPDATA'], 'MediaWidget', '.spotify_cache')
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        token_info = json.load(f)
                    if token_info.get('access_token'):
                        self.spotify = spotipy.Spotify(auth=token_info['access_token'])
                        self.is_spotify_connected = True
                        logging.info("Loaded existing token")
                        return
                except Exception as e:
                    logging.error(f"Error loading token: {str(e)}")

            self.show_spotify_login()
            
        except Exception as e:
            self.is_spotify_connected = False
            logging.error(f"Error initializing Spotify client: {str(e)}")
            self.show_spotify_login()

    def show_spotify_login(self):
        """Show Spotify login dialog"""
        self.status_label.setText("Spotify not connected")
        self.song_label.setText("")
        self.artist_label.setText("")
        self.update_button_states()

    def start_spotify_auth(self):
        """Start Spotify authentication process with PKCE"""
        try:
            # Read client ID from file
            if not os.path.exists('spotify_credentials.json'):
                logging.error("Spotify credentials file not found")
                self.show_tooltip("Error: Spotify credentials not found. Please contact support.")
                return

            with open('spotify_credentials.json', 'r') as f:
                credentials = json.load(f)

            if 'client_id' not in credentials:
                logging.error("Client ID not found in credentials file")
                self.show_tooltip("Error: Invalid credentials format. Please contact support.")
                return

            # Generate PKCE code verifier and challenge
            code_verifier = self.generate_code_verifier()
            code_challenge = self.generate_code_challenge(code_verifier)

            # Store code verifier in settings
            self.settings.setValue('code_verifier', code_verifier)
            # Generate and store a unique ID for this auth attempt
            code_id = str(int(time.time() * 1000))
            self.settings.setValue('code_id', code_id)

            # Construct authorization URL
            auth_url = 'https://accounts.spotify.com/authorize'
            params = {
                'client_id': credentials['client_id'],
                'response_type': 'code',
                'redirect_uri': credentials['redirect_uri'],
                'scope': 'user-read-playback-state user-modify-playback-state',
                'code_challenge_method': 'S256',
                'code_challenge': code_challenge,
                'state': code_id  # Add the code_id as state parameter
            }
            
            auth_url = f"{auth_url}?{urlencode(params)}"
            
            # Open browser for authorization
            import webbrowser
            webbrowser.open(auth_url)
            
            # Start polling for the token
            self.poll_for_token(code_verifier, credentials)
            
        except Exception as e:
            logging.error(f"Error during Spotify authentication: {str(e)}")
            self.show_tooltip("Failed to connect to Spotify. Please try again.")

    def poll_for_token(self, code_verifier, credentials):
        """Poll for the authorization code from the callback server"""
        try:
            code_id = self.settings.value('code_id')
            if not code_id:
                logging.error("No code ID found")
                return

            # Use the correct API endpoint from credentials
            base_url = credentials['redirect_uri'].rstrip('/')
            api_url = f"{base_url}/check-code"  # Remove /api/ prefix
            logging.info(f"Polling URL: {api_url}")
            
            response = requests.get(f"{api_url}?id={code_id}")
            print(response)
            logging.info(f"Response status: {response.status_code}")
            logging.info(f"Response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if 'code' in data:
                    code = data['code']
                    logging.info("Received authorization code")
                    self.exchange_code_for_token(code, code_verifier, credentials)
                    return
                else:
                    logging.error("No code in response")
            elif response.status_code == 404:
                # Code not found yet, continue polling
                logging.info("Code not found yet, continuing to poll...")
            else:
                logging.error(f"Error polling for code: {response.status_code}")
            
            # If no code yet or error, retry after a delay
            QTimer.singleShot(2000, lambda: self.poll_for_token(code_verifier, credentials))
            
        except Exception as e:
            logging.error(f"Error polling for token: {str(e)}")
            # Retry on error
            QTimer.singleShot(2000, lambda: self.poll_for_token(code_verifier, credentials))

    def exchange_code_for_token(self, code, code_verifier, credentials):
        """Exchange the authorization code for an access token"""
        try:
            token_url = 'https://accounts.spotify.com/api/token'
            data = {
                'client_id': credentials['client_id'],
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': credentials['redirect_uri'],
                'code_verifier': code_verifier
            }
            
            response = requests.post(token_url, data=data)
            token_info = response.json()
            
            if 'access_token' in token_info:
                # Save token
                cache_path = os.path.join(os.environ['APPDATA'], 'MediaWidget', '.spotify_cache')
                with open(cache_path, 'w') as f:
                    json.dump(token_info, f)
                
                self.spotify = spotipy.Spotify(auth=token_info['access_token'])
                self.is_spotify_connected = True
                self.reconnect_attempts = 0
                logging.info("Spotify authentication successful")
                self.update_button_states()
                self.show_tooltip("Successfully connected to Spotify!")
            else:
                raise Exception("Failed to get access token")
            
        except Exception as e:
            logging.error(f"Error exchanging code for token: {str(e)}")
            self.show_tooltip("Failed to connect to Spotify. Please try again.")

    def check_media_players(self):
        """Check Spotify playback status using Web API"""
        try:
            self.is_spotify_running = any(
                proc.info['name'].lower() == 'spotify.exe'
                for proc in psutil.process_iter(['name'])
            )

            if not self.is_spotify_running:
                self.status_label.setText("Spotify is not running")
                self.song_label.setText("")
                self.artist_label.setText("")
                self.update_button_states()
                return

            if not self.is_spotify_connected:
                self.show_spotify_login()
                return

            if self.spotify and self.is_spotify_connected:
                current = self.spotify.current_playback()
                if current and current['is_playing']:
                    track = current['item']
                    if track:
                        song = track['name']
                        artist = track['artists'][0]['name']
                        current_info = f"{song} - {artist}"
                        
                        # Only update if track info has changed
                        if current_info != self.last_track_info:
                            self.status_label.setText("Now playing on Spotify")
                            self.song_label.setText(self.truncate_text(song, 25))
                            self.artist_label.setText(self.truncate_text(artist, 30))
                            self.current_playback_state = current
                            self.play_button.setIcon(QIcon("icons/pause.png"))
                            self.last_track_info = current_info
                            logging.info(f"Now playing: {current_info}")
                        return
                    else:
                        self.status_label.setText("No track playing")
                else:
                    self.status_label.setText("Spotify is paused")
                    self.play_button.setIcon(QIcon("icons/play.png"))
            else:
                self.status_label.setText("Spotify is not connected")
                self.show_spotify_login()
        except Exception as e:
            logging.error(f"Error checking Spotify status: {str(e)}")
            self.status_label.setText("Error connecting to Spotify")
            self.show_spotify_login()
            
        self.update_button_states()

    def truncate_text(self, text, max_length=30):
        """Truncate text with ellipsis if it's too long"""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def previous_track(self):
        """Send previous track command"""
        if not self.is_spotify_running:
            self.show_tooltip("Spotify is not running")
            return

        if self.spotify and self.is_spotify_connected:
            try:
                self.spotify.previous_track()
                logging.info("Skipped to previous track")
            except Exception as e:
                logging.error(f"Error skipping to previous track: {str(e)}")
                self.show_tooltip("Failed to skip track")
        else:
            self.send_media_key(win32con.VK_MEDIA_PREV_TRACK)

    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.is_spotify_running:
            self.show_tooltip("Spotify is not running")
            return

        if self.spotify and self.is_spotify_connected:
            try:
                current = self.spotify.current_playback()
                if current and current['is_playing']:
                    self.spotify.pause_playback()
                    self.play_button.setIcon(QIcon("icons/play.png"))
                    logging.info("Playback paused")
                else:
                    self.spotify.start_playback()
                    self.play_button.setIcon(QIcon("icons/pause.png"))
                    logging.info("Playback started")
            except Exception as e:
                logging.error(f"Error toggling playback: {str(e)}")
                self.show_tooltip("Failed to control playback")
        else:
            self.send_media_key(win32con.VK_MEDIA_PLAY_PAUSE)
            # Toggle icon
            if self.play_button.icon().pixmap(32, 32).toImage() == QIcon("icons/play.png").pixmap(32, 32).toImage():
                self.play_button.setIcon(QIcon("icons/pause.png"))
            else:
                self.play_button.setIcon(QIcon("icons/play.png"))

    def next_track(self):
        """Send next track command"""
        if not self.is_spotify_running:
            self.show_tooltip("Spotify is not running")
            return

        if self.spotify and self.is_spotify_connected:
            try:
                self.spotify.next_track()
                logging.info("Skipped to next track")
            except Exception as e:
                logging.error(f"Error skipping to next track: {str(e)}")
                self.show_tooltip("Failed to skip track")
        else:
            self.send_media_key(win32con.VK_MEDIA_NEXT_TRACK)

    def set_volume(self, value):
        """Set system volume"""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(value / 100.0, None)
            logging.info(f"Volume set to {value}%")
        except Exception as e:
            logging.error(f"Error setting volume: {str(e)}")
            self.show_tooltip("Failed to set volume")

    def send_media_key(self, key):
        """Send media key command to Windows"""
        try:
            win32api.keybd_event(key, 0, 0, 0)  # Key down
            win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)  # Key up
            logging.info(f"Sent media key: {key}")
        except Exception as e:
            logging.error(f"Error sending media key: {str(e)}")
            self.show_tooltip("Failed to send media command")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.drag_start_pos = self.pos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPos() - self.oldPos
            new_pos = self.drag_start_pos + delta
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self.oldPos = None
        self.drag_start_pos = None

    def closeEvent(self, event):
        """Handle window close event"""
        self.hotkey_manager.stop()  # Clean up hotkeys
        self.save_settings()
        event.accept()

    def show_account_menu(self):
        """Show account menu with disconnect option"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                border: none;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        if self.is_spotify_connected:
            disconnect_action = menu.addAction("Disconnect Spotify")
            disconnect_action.triggered.connect(self.disconnect_spotify)
        else:
            connect_action = menu.addAction("Connect to Spotify")
            connect_action.triggered.connect(self.start_spotify_auth)
        
        # Show menu below the account button
        menu.exec_(self.account_button.mapToGlobal(
            QPoint(0, self.account_button.height())
        ))

    def disconnect_spotify(self):
        """Disconnect from Spotify and clear cache"""
        try:
            # Clear Spotify cache
            cache_path = os.path.join(os.environ['APPDATA'], 'MediaWidget', '.spotify_cache')
            if os.path.exists(cache_path):
                os.remove(cache_path)
            
            # Reset state
            self.is_spotify_connected = False
            self.spotify = None
            self.current_playback_state = None
            self.last_track_info = None
            
            # Clear UI
            self.status_label.setText("Spotify disconnected")
            self.song_label.setText("")
            self.artist_label.setText("")
            
            # Show login UI
            self.show_spotify_login()
            
            logging.info("Successfully disconnected from Spotify")
            self.show_tooltip("Disconnected from Spotify")
            
        except Exception as e:
            logging.error(f"Error disconnecting from Spotify: {str(e)}")
            self.show_tooltip("Error disconnecting from Spotify")

    def _connect_hotkey_signals(self):
        """Connect hotkey signals to widget functions"""
        self.hotkey_manager.play_pause_triggered.connect(self.toggle_playback)
        self.hotkey_manager.next_track_triggered.connect(self.next_track)
        self.hotkey_manager.prev_track_triggered.connect(self.previous_track)
        self.hotkey_manager.volume_up_triggered.connect(lambda: self.set_volume(min(100, self.volume_slider.value() + 5)))
        self.hotkey_manager.volume_down_triggered.connect(lambda: self.set_volume(max(0, self.volume_slider.value() - 5)))
        
    def show_hotkey_settings(self):
        """Show the hotkey settings dialog"""
        dialog = HotkeySettingsDialog(self.hotkey_manager, self)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MediaWidget()
    widget.show()
    sys.exit(app.exec_()) 