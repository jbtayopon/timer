#define MyAppName "TPX - Timer Pro X"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "June Bernard Tayopon"
#define MyAppExeName "TPX.exe"

#define MySourceDir "C:\xampp\htdocs\timer"

[Setup]
AppId={{TPX-TIMER-PRO-X}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\TPX
DefaultGroupName={#MyAppName}

OutputDir={#MySourceDir}\installer
OutputBaseFilename=TPX-Setup

Compression=lzma
SolidCompression=yes

WizardStyle=modern

PrivilegesRequired=admin

UninstallDisplayIcon={app}\TPX.exe

[Files]
Source: "{#MySourceDir}\dist\TPX.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\TPX.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\TPX.exe"

[Run]
Filename: "{app}\TPX.exe"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"