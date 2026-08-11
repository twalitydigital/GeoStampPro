[Setup]
#define AppVersion "1.0.0"

#ifndef TargetArch
#define TargetArch "x64"
#endif

#if TargetArch == "x64"
#define SetupArchitecturesAllowed "x64compatible"
#define SetupArchitecturesInstallIn64BitMode "x64compatible"
#elif TargetArch == "arm64"
#define SetupArchitecturesAllowed "arm64"
#define SetupArchitecturesInstallIn64BitMode "arm64"
#elif TargetArch == "x86"
#define SetupArchitecturesAllowed "x86compatible and not x64compatible"
#define SetupArchitecturesInstallIn64BitMode ""
#else
#error Unsupported TargetArch. Use x64, arm64, or x86.
#endif

AppName=Twality GMark Pro
AppVersion={#AppVersion}
DefaultDirName={autopf}\Twality GMark Pro
DefaultGroupName=Twality GMark Pro
OutputDir=.
OutputBaseFilename=TwalityGMarkProSetup-{#TargetArch}
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\TwalityGMark.exe
LicenseFile=..\LICENSE.txt
AppPublisher=Twality Digital Solutions LLP
AppPublisherURL=https://www.twality.com
AppSupportURL=https://www.twality.com
AppUpdatesURL=https://www.twality.com
ArchitecturesAllowed={#SetupArchitecturesAllowed}
#if SetupArchitecturesInstallIn64BitMode != ""
ArchitecturesInstallIn64BitMode={#SetupArchitecturesInstallIn64BitMode}
#endif

[Files]
Source: "..\dist\TwalityGMark\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Twality GMark Pro"; Filename: "{app}\TwalityGMark.exe"
Name: "{commondesktop}\Twality GMark Pro"; Filename: "{app}\TwalityGMark.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\TwalityGMark.exe"; Description: "Launch Twality GMark Pro"; Flags: nowait postinstall skipifsilent
