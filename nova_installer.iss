; Inno Setup Script for NOVA AI
; Compile this script using Inno Setup Compiler to generate the Windows Setup Wizard (.exe)

[Setup]
AppName=NOVA AI
AppVersion=1.0.0
AppPublisher=Muhammad Alyan
DefaultDirName={autopf}\NOVA AI
DefaultGroupName=NOVA AI
OutputDir=installer_output
OutputBaseFilename=NOVA_AI_Setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\NOVA_AI.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all compiled files from the PyInstaller dist directory
Source: "dist\NOVA_AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Create shortcuts in Start Menu and Desktop
Name: "{group}\NOVA AI"; Filename: "{app}\NOVA_AI.exe"
Name: "{autodesktop}\NOVA AI"; Filename: "{app}\NOVA_AI.exe"; Tasks: desktopicon

[Run]
; Run the app automatically after the installer exits
Filename: "{app}\NOVA_AI.exe"; Description: "{cm:LaunchProgram,NOVA AI}"; Flags: nowait postinstall skipifsilent
