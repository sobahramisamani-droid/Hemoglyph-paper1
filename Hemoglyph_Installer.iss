; =====================================================================
; HEMOGLYPH MEDICAL CDSS - PROFESSIONAL WINDOWS INSTALLER SCRIPT
; Engine: Inno Setup 6.x
; Platform: Windows 10/11 x64
; Author: Sobhan Bahrami
; =====================================================================

#define MyAppName "Hemoglyph Clinical CDSS"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "Sobhan Bahrami"
#define MyAppExeName "Hemoglyph.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".hgc"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{D37E8B32-9F1C-4B2A-94A1-E7C1F2B48D90}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://hemoglyph.org
AppSupportURL=https://hemoglyph.org/support
AppUpdatesURL=https://hemoglyph.org/updates
DefaultDirName={localappdata}\Programs\Hemoglyph
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Hemoglyph_Setup_v1.3.1
SetupIconFile=app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Source points to the compiled Nuitka standalone output directory (excludes developer databases/logs)
Source: "dist\app.dist\*"; DestDir: "{app}"; Excludes: "*.log, hemoglyph.db, nuitka-crash-report.xml"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
