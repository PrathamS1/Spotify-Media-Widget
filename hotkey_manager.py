import keyboard
import logging
from PyQt5.QtCore import QObject, pyqtSignal

class HotkeyManager(QObject):
    # Signals for hotkey events
    play_pause_triggered = pyqtSignal()
    next_track_triggered = pyqtSignal()
    prev_track_triggered = pyqtSignal()
    volume_up_triggered = pyqtSignal()
    volume_down_triggered = pyqtSignal()

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.hotkeys = {}
        self.load_hotkey_settings()
        
    def load_hotkey_settings(self):
        """Load hotkey settings from widget settings"""
        default_hotkeys = {
            'play_pause': 'ctrl+alt+p',
            'next_track': 'ctrl+alt+n',
            'prev_track': 'ctrl+alt+b',
            'volume_up': 'ctrl+alt+up',
            'volume_down': 'ctrl+alt+down'
        }
        
        saved_hotkeys = self.widget.settings.value('hotkeys', default_hotkeys)
        self.hotkeys = saved_hotkeys
        
    def save_hotkey_settings(self):
        """Save hotkey settings to widget settings"""
        self.widget.settings.setValue('hotkeys', self.hotkeys)
        
    def start(self):
        """Start listening for hotkeys"""
        try:
            # Register hotkeys
            keyboard.add_hotkey(self.hotkeys['play_pause'], self._on_play_pause)
            keyboard.add_hotkey(self.hotkeys['next_track'], self._on_next_track)
            keyboard.add_hotkey(self.hotkeys['prev_track'], self._on_prev_track)
            keyboard.add_hotkey(self.hotkeys['volume_up'], self._on_volume_up)
            keyboard.add_hotkey(self.hotkeys['volume_down'], self._on_volume_down)
            
            logging.info("Hotkeys registered successfully")
        except Exception as e:
            logging.error(f"Error registering hotkeys: {str(e)}")
            
    def stop(self):
        """Stop listening for hotkeys"""
        try:
            keyboard.unhook_all()
            logging.info("Hotkeys unregistered successfully")
        except Exception as e:
            logging.error(f"Error unregistering hotkeys: {str(e)}")
            
    def _on_play_pause(self):
        """Handle play/pause hotkey"""
        logging.info("Play/Pause hotkey triggered")
        self.play_pause_triggered.emit()
        
    def _on_next_track(self):
        """Handle next track hotkey"""
        logging.info("Next track hotkey triggered")
        self.next_track_triggered.emit()
        
    def _on_prev_track(self):
        """Handle previous track hotkey"""
        logging.info("Previous track hotkey triggered")
        self.prev_track_triggered.emit()
        
    def _on_volume_up(self):
        """Handle volume up hotkey"""
        logging.info("Volume up hotkey triggered")
        self.volume_up_triggered.emit()
        
    def _on_volume_down(self):
        """Handle volume down hotkey"""
        logging.info("Volume down hotkey triggered")
        self.volume_down_triggered.emit()
        
    def update_hotkey(self, action, new_hotkey):
        """Update a specific hotkey"""
        try:
            # Remove old hotkey
            if action in self.hotkeys:
                keyboard.remove_hotkey(self.hotkeys[action])
            
            # Add new hotkey
            keyboard.add_hotkey(new_hotkey, getattr(self, f'_on_{action}'))
            self.hotkeys[action] = new_hotkey
            self.save_hotkey_settings()
            
            logging.info(f"Updated hotkey for {action} to {new_hotkey}")
            return True
        except Exception as e:
            logging.error(f"Error updating hotkey: {str(e)}")
            return False 