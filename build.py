import os
import shutil
import subprocess
import sys

def find_nsis():
    """Find NSIS installation"""
    # Common NSIS installation paths
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\NSIS\makensis.exe"
    ]
    
    # Check if makensis is in PATH
    try:
        subprocess.run(["makensis", "/VERSION"], capture_output=True, check=True)
        return "makensis"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check common installation paths
    for path in nsis_paths:
        if os.path.exists(path):
            return path
    
    return None

def clean_build():
    """Clean build and dist directories"""
    print("Cleaning build directories...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

def create_executable():
    """Create executable using PyInstaller"""
    print("Creating executable...")
    subprocess.run([
        "pyinstaller",
        "--noconsole",
        "--icon=icons/app.ico",
        "--add-data", "icons/*;icons/",
        "--add-data", "spotify_credentials.json;.",
        "--name", "MediaWidget",
        "--clean",  # Clean PyInstaller cache
        "--onefile",  # Create a single executable
        "media_widget.py"
    ], check=True)  # Add check=True to raise error if command fails

def copy_additional_files():
    """Copy additional files to dist directory"""
    print("Copying additional files...")
    dist_dir = "dist/MediaWidget"
    
    # Create dist directory if it doesn't exist
    os.makedirs(dist_dir, exist_ok=True)
    
    # Create icons directory
    icons_dir = os.path.join(dist_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    # Copy icons
    for icon in os.listdir("icons"):
        shutil.copy2(f"icons/{icon}", icons_dir)
    
    # Copy README and LICENSE
    if os.path.exists("README.md"):
        shutil.copy2("README.md", dist_dir)
    if os.path.exists("LICENSE.txt"):
        shutil.copy2("LICENSE.txt", dist_dir)
    
    # Ensure spotify_credentials.json is copied
    if os.path.exists("spotify_credentials.json"):
        shutil.copy2("spotify_credentials.json", dist_dir)
    
    print(f"Files copied to {dist_dir}")

def create_installer():
    """Create installer using NSIS"""
    print("Creating installer...")
    
    # Find NSIS
    nsis_path = find_nsis()
    if not nsis_path:
        print("Error: NSIS (makensis) not found!")
        print("Please ensure NSIS is installed and either:")
        print("1. Add NSIS to your system PATH, or")
        print("2. Install NSIS to one of these locations:")
        print("   - C:\\Program Files (x86)\\NSIS")
        print("   - C:\\Program Files\\NSIS")
        print("   - C:\\NSIS")
        print("\nDownload NSIS from: https://nsis.sourceforge.io/Download")
        sys.exit(1)
    
    try:
        print(f"Using NSIS at: {nsis_path}")
        subprocess.run([nsis_path, "installer.nsi"], check=True)
        print("Installer created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error creating installer: {e}")
        sys.exit(1)

def main():
    """Main build process"""
    print("Starting build process...")
    
    # Check for required files
    required_files = [
        "icons/app.ico",
        "spotify_credentials.json",
        "icons/account.png",
        "icons/account_connected.png",
        "icons/play.png",
        "icons/pause.png",
        "icons/next.png",
        "icons/prev.png"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("Error: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        sys.exit(1)
    
    try:
        # Clean previous builds
        clean_build()
        
        # Create executable
        create_executable()
        
        # Copy additional files
        copy_additional_files()
        
        # Create installer
        create_installer()
        
        print("\nBuild and installer creation completed successfully!")
        print("You can find:")
        print("1. The executable in the 'dist/MediaWidget' directory")
        print("2. The installer as 'MediaWidgetSetup.exe' in the current directory")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError during build process: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 