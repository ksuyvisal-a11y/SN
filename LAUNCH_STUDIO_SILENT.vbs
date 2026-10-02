' SN TOOL - STUDIO PRO Silent Launcher
' Opens SN TOOL directly without showing a black Command Prompt window
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strDir

' Launch SN_TOOL.bat invisibly (0 = Hide window)
WshShell.Run Chr(34) & strDir & "\SN_TOOL.bat" & Chr(34), 0, False
