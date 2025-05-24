# Spotify Media Widget

A lightweight desktop widget for controlling Spotify playback with a modern, minimal UI and global hotkeys. This project is designed as a learning tool, allowing users to set up their own Spotify Developer account and customize the widget according to their needs.

## Important Notes
⚠️ **Spotify Premium Required**: This widget requires a Spotify Premium account to control playback (play/pause, next/previous). This is a limitation of the Spotify Web API, not the widget itself.

⚠️ **Developer Account Required**: You need to create your own Spotify Developer account and set up your own application to use this widget. This is a learning project, and you should not use someone else's client ID.

## Features

- 🎵 Control Spotify playback (play/pause, next/previous) - Requires Premium
- 📱 View currently playing track (works with Free and Premium)
- ⌨️ Global hotkeys for media control (Premium features require Premium account)
- 🔊 System volume control (works with any account)
- 🎨 Modern, minimal UI with glassmorphism effect
- 💾 Persistent settings (window position, volume, hotkeys)
- 🔄 Automatic reconnection
- 🚀 Startup with Windows option
- 📦 Build system included for creating installers

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/media-widget.git
   cd media-widget
   ```

2. **Install Dependencies**
   ```bash
   # Core dependencies
   pip install PyQt5==5.15.9
   pip install spotipy==2.23.0
   pip install keyboard==0.13.5
   pip install psutil==5.9.5
   pip install pywin32==306
   pip install pycaw==20230407
   pip install requests==2.31.0

   # Build dependencies (optional)
   pip install pyinstaller==6.1.0
   ```
   If the specified versions don't work, install simply like `pip install PyQt5`.
3. **Set Up Spotify Developer Account**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Log in with your Spotify account
   - Click "Create App"
   - Fill in the app details:
     - App name: "Media Widget"
     - App description: "Desktop widget for Spotify control"
     - Redirect URI: `http://localhost:8888/callback`
   - After creating the app, you'll get a Client ID
   - Create a `spotify_credentials.json` file or you can rename the `spotify_credentials.json.template`:
     ```json
     {
         "client_id": "YOUR_CLIENT_ID",
         "redirect_uri": "http://localhost:8888/callback"
     }
     ```
   - You can use my redirect URL as it has been deployed already:
      ```json
      {
         "redirect_url": "https://spotify-callback-omega.vercel.app/"
      }
      ```

4. **Run the Widget**
   ```bash
   python media_widget.py
   ```

## Building the Project
#### Make sure that you have created the `spotify_credentials.json` file as it is necessary for performing build

### Option 1: Using PyInstaller (Recommended)
1. Install PyInstaller (if not already installed):
   ```bash
   pip install pyinstaller==6.1.0
   ```
2. Build the executable:
   ```bash
   pyinstaller --onefile --windowed --icon=icons/app.ico media_widget.py
   ```

3. The executable will be in the `dist` folder

### Option 2: Creating an Installer
1. Install NSIS (Nullsoft Scriptable Install System)
2. Run the build script:
   ```bash
   python build.py
   ```
3. The `.exe` installer will be created in the `root` folder.

## First Run

1. Launch Media Widget
2. Click the account icon and select "Connect to Spotify"
3. A browser window will open
4. Log in to your Spotify account
5. Grant the requested permissions
6. The widget will automatically connect to Spotify

## Usage

### Controls
- **Play/Pause**: Click the play button or use `Ctrl + Alt + P`
- **Next Track**: Click the next button or use `Ctrl + Alt + N`
- **Previous Track**: Click the previous button or use `Ctrl + Alt + B`
- **Volume Up**: Use `Ctrl + Alt + Up`
- **Volume Down**: Use `Ctrl + Alt + Down`
- **Volume**: Use the slider
- **Move**: Drag the widget
- **Close**: Click the × button
- **Settings**: Click the settings icon to customize hotkeys

### Features
- Window position is remembered
- Volume level persists
- Hotkey settings are saved
- Starts with Windows (optional)
- Auto-reconnects to Spotify
- Global hotkeys work in any application
- Modern glassmorphism UI design

## Customizing Hotkeys

1. Click the settings icon in the widget
2. Click on any hotkey button
3. Press your desired key combination (you need to press the combination together at once)
4. Click "Save" to apply changes
5. Click "Reset" to restore default hotkeys

## Development

### Project Structure
```
media-widget/
├── media_widget.py      # Main application
├── hotkey_manager.py    # Hotkey handling
├── hotkey_settings_dialog.py  # Hotkey settings UI
├── icons/               # Application icons
├── build.py             # Installer build script
├── installer.nsi        # Installer build script
└── README.md            # Project documentation
├── spotify_credentials.json  # Required credentials for widget
```

### Required Permissions

For the widget to control Spotify playback, ensure these permissions are enabled in your Spotify Developer Dashboard:

1. **For Users**
   - **Premium Account Required** for playback control features
   - Free accounts can still:
     - View currently playing tracks
     - Control system volume
     - Use the widget interface
   - Users must have Spotify Desktop app installed and running
   - Users must be logged into their Spotify account
   - Users must have an active device (Spotify Desktop app must be open in background)

## Troubleshooting Player Control

If the widget connects but can't control playback:

1. **Check Spotify Account Type**
   - Premium account is required for playback control
   - Free accounts will see "Premium Required" errors in logs
   - Free accounts can still view track information

2. **Check Spotify Desktop App**
   - Ensure Spotify Desktop app is running
   - Try restarting Spotify Desktop app
   - Make sure you're logged in to the correct account

3. **Check Permissions**
   - Disconnect from the widget
   - Clear the cache:
     - Delete `.spotify_cache` in `%APPDATA%\MediaWidget\`
   - Reconnect to Spotify
   - When the browser opens, ensure you accept ALL permissions

4. **Check Active Device**
   - Open Spotify Desktop app
   - Play any song
   - Check if the widget shows the current song
   - If not, try:
     - Pause/play in Spotify Desktop app
     - Switch to a different song
     - Restart Spotify Desktop app

5. **Common Issues**
   - If controls don't work:
     - Check if Spotify Desktop app is the active device
     - Try playing a song in Spotify Desktop app first
     - Ensure no other app is controlling Spotify
   - If song info doesn't update:
     - Check if Spotify Desktop app is playing
     - Try refreshing the widget
     - Check the log file for errors

6. **Hotkeys not working**
   - Check if the hotkeys conflict with other applications
   - Try resetting to default hotkeys
   - Ensure the widget is running

### Logging
- Logs are stored in `%APPDATA%\MediaWidget\media_widget.log`
- Check this file for detailed error messages

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Sharing the App

If you want to share this app with others, you need to:

1. **Add Users to Your Spotify App**
   - Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Select your app
   - Click "Settings"
   - Scroll to "User Management"
   - Click "Add New User"
   - Add the email address of the person you're sharing with
   - They will receive an email invitation to use your app

2. **Common Connection Issues**
   - If users get a 403 error, ensure they:
     - Have accepted the app invitation email
     - Are using the correct `spotify_credentials.json` file
     - Have Spotify Desktop app installed and running
     - Are logged into their Spotify account
   - If issues persist:
     - Check the log file in `%APPDATA%\MediaWidget\media_widget.log`
     - Try disconnecting and reconnecting
     - Ensure no firewall is blocking the connection 

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Spotify Web API
- PyQt5
- Windows Media Control
- Keyboard library for global hotkeys

