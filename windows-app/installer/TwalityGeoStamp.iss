[Setup]
AppName=Twality GeoStamp
AppVersion=1.0.0
DefaultDirName={autopf}\Twality GeoStamp
DefaultGroupName=Twality GeoStamp
OutputDir=.
OutputBaseFilename=TwalityGeoStampSetup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\TwalityGeoStamp.exe

[Files]
Source: "..\dist\TwalityGeoStamp\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Twality GeoStamp"; Filename: "{app}\TwalityGeoStamp.exe"
Name: "{commondesktop}\Twality GeoStamp"; Filename: "{app}\TwalityGeoStamp.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\TwalityGeoStamp.exe"; Description: "Launch Twality GeoStamp"; Flags: nowait postinstall skipifsilent
