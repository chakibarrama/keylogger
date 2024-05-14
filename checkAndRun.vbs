Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcessList = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'pythonw.exe'")

isRunning = False
For Each objProcess in colProcessList
    If InStr(objProcess.CommandLine, "C:\path\to\your_script.py") > 0 Then
        isRunning = True
        Exit For
    End If
Next

If Not isRunning Then
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.Run "pythonw.exe C:\path\to\your_script.py", 0
    Set WshShell = Nothing
End If
