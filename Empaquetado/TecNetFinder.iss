#define MyAppName "TecNet Finder"
#define MyAppVersion "1.2.1"
#define MyAppPublisher "RobDev512"
#define MyAppExeName "TecNetFinder.exe"

[Setup]
AppId={{E97A8C8D-5D55-4B75-9A54-0E9E11417E64}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\TecNet Finder
DefaultGroupName=TecNet Finder
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\dist\Instalador
OutputBaseFilename=TecNet Finder {#MyAppVersion} Setup
SetupIconFile=..\Recursos\Marca\LogoTNF.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos adicionales:"; Flags: unchecked

[Files]
Source: "..\dist\TecNetFinder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TecNet Finder"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\TecNet Finder"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir TecNet Finder"; Flags: nowait postinstall skipifsilent
