; Inno Setup script for File Organizer Agent (Day 2 - Windows).
; Must be compiled on Windows with Inno Setup (iscc.exe), after
; scripts/build_windows_exe.sh has produced dist/File Organizer Agent/.
;
; This is a starter script - fill in real values before first release.
; Never requires admin privileges to install/run.

#define MyAppName "File Organizer Agent"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "File Organizer Agent contributors"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=File Organizer Agent Setup
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\..\dist\File Organizer Agent\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\File Organizer Agent.exe"

[Tasks]
Name: "launchatlogin"; Description: "Launch at login"; GroupDescription: "Options:"; Flags: unchecked
