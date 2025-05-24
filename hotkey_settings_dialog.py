from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
import keyboard
import time

class HotkeySettingsDialog(QDialog):
    def __init__(self, hotkey_manager, parent=None):
        super().__init__(parent)
        self.hotkey_manager = hotkey_manager
        self.current_hotkey = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Hotkey Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Create hotkey settings for each action
        self.hotkey_widgets = {}
        for action, hotkey in self.hotkey_manager.hotkeys.items():
            action_layout = QHBoxLayout()
            
            # Action label
            label = QLabel(action.replace('_', ' ').title())
            action_layout.addWidget(label)
            
            # Hotkey button
            hotkey_btn = QPushButton(hotkey)
            hotkey_btn.clicked.connect(lambda checked, a=action, b=hotkey_btn: self.start_hotkey_capture(a, b))
            action_layout.addWidget(hotkey_btn)
            
            # Reset button
            reset_btn = QPushButton("Reset")
            reset_btn.clicked.connect(lambda checked, a=action, b=hotkey_btn: self.reset_hotkey(a, b))
            action_layout.addWidget(reset_btn)
            
            self.hotkey_widgets[action] = hotkey_btn
            layout.addLayout(action_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def start_hotkey_capture(self, action, button):
        """Start capturing a new hotkey"""
        if self.current_hotkey:
            return
            
        self.current_hotkey = action
        button.setText("Press keys...")
        button.setStyleSheet("background-color: #4CAF50; color: white;")
        
        # Start listening for key combination
        keyboard.hook(self.on_key_event)
        
    def on_key_event(self, event):
        """Handle key events during hotkey capture"""
        if not self.current_hotkey or not event.event_type == keyboard.KEY_DOWN:
            return
            
        # Get all currently pressed keys
        pressed_keys = keyboard.get_hotkey_name()
        
        # Wait a short moment to capture modifier keys
        time.sleep(0.1)
        
        # Get the final key combination
        final_keys = keyboard.get_hotkey_name()
        
        if final_keys:
            button = self.hotkey_widgets[self.current_hotkey]
            button.setText(final_keys)
            button.setStyleSheet("")
            
            # Update the hotkey
            self.hotkey_manager.update_hotkey(self.current_hotkey, final_keys)
            
            # Stop capturing
            keyboard.unhook(self.on_key_event)
            self.current_hotkey = None
            
    def reset_hotkey(self, action, button):
        """Reset a hotkey to its default value"""
        default_hotkeys = {
            'play_pause': 'ctrl+alt+p',
            'next_track': 'ctrl+alt+n',
            'prev_track': 'ctrl+alt+b',
            'volume_up': 'ctrl+alt+up',
            'volume_down': 'ctrl+alt+down'
        }
        
        if action in default_hotkeys:
            button.setText(default_hotkeys[action])
            self.hotkey_manager.update_hotkey(action, default_hotkeys[action])
            
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.current_hotkey:
            keyboard.unhook(self.on_key_event)
        event.accept()