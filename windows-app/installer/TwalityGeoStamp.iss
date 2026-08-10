[Setup]
AppName=Twality GeoStamp Pro
AppVersion=1.0.0
DefaultDirName={autopf}\Twality GeoStamp Pro
DefaultGroupName=Twality GeoStamp Pro
OutputDir=.
OutputBaseFilename=TwalityGeoStampProSetup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\TwalityGeoStamp.exe
LicenseFile=..\LICENSE.txt
AppPublisher=Twality Digital Solutions LLP
AppPublisherURL=https://www.twality.com
AppSupportURL=https://www.twality.com
AppUpdatesURL=https://www.twality.com

[Files]
Source: "..\dist\TwalityGeoStamp\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Twality GeoStamp Pro"; Filename: "{app}\TwalityGeoStamp.exe"
Name: "{commondesktop}\Twality GeoStamp Pro"; Filename: "{app}\TwalityGeoStamp.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\TwalityGeoStamp.exe"; Description: "Launch Twality GeoStamp Pro"; Flags: nowait postinstall skipifsilent
