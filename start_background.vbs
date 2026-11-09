Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "d:\auto publish facebook"
WshShell.Run "python main.py", 0, False