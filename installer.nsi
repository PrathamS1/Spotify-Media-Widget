!include "MUI2.nsh"
!include "FileFunc.nsh"

; General settings
Name "Media Widget"
OutFile "MediaWidgetSetup.exe"
InstallDir "$PROGRAMFILES\Media Widget"
InstallDirRegKey HKCU "Software\Media Widget" "Install_Dir"
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "icons\app.ico"
!define MUI_UNICON "icons\app.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy main executable
    File "dist\MediaWidget.exe"
    
    ; Copy additional files
    SetOutPath "$INSTDIR\icons"
    File /r "icons\*.*"
    
    ; Copy credentials if they exist
    SetOutPath "$INSTDIR"
    File "spotify_credentials.json"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\Media Widget"
    CreateShortcut "$SMPROGRAMS\Media Widget\Media Widget.lnk" "$INSTDIR\MediaWidget.exe"
    CreateShortcut "$SMPROGRAMS\Media Widget\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Create desktop shortcut
    CreateShortcut "$DESKTOP\Media Widget.lnk" "$INSTDIR\MediaWidget.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\Media Widget" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Widget" "DisplayName" "Media Widget"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Widget" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Widget" "DisplayIcon" "$INSTDIR\MediaWidget.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Widget" "Publisher" "Your Name"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Widget" "DisplayVersion" "1.0.0"
    
    ; Add to startup
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "MediaWidget" "$INSTDIR\MediaWidget.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\Media Widget\Media Widget.lnk"
    Delete "$SMPROGRAMS\Media Widget\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Media Widget"
    Delete "$DESKTOP\Media Widget.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Widget"
    DeleteRegKey HKCU "Software\Media Widget"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "MediaWidget"
SectionEnd 