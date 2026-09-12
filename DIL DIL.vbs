Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = ScriptDir
WshShell.Run """C:\Users\PMLS\AppData\Local\Programs\Python\Python312\pythonw.exe"" main.py", 0, False
