; installer.iss
[Setup]
AppId={{8F9A2B4C-5D6E-4A1B-9C8D-7E6F5A4B3C2D}
AppName=PulseTube Studio
AppVersion=1.0.0
AppPublisher=PulseTube Studio (SKJ)
DefaultDirName={autopf}\PulseTube
DefaultGroupName=PulseTube Studio
DisableProgramGroupPage=yes
OutputDir=installer_out
OutputBaseFilename=PulseTube_Setup_v1.0.0
SetupIconFile=icon.ico
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
CloseApplications=force

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\PulseTube\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "web\*"; DestDir: "{app}\web"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\PulseTube Studio"; Filename: "{app}\PulseTube.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\PulseTube Studio"; Filename: "{app}\PulseTube.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\PulseTube.exe"; Description: "{cm:LaunchProgram,PulseTube Studio}"; Flags: nowait postinstall skipifsilent