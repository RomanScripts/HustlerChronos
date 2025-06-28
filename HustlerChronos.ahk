#NoEnv
#SingleInstance, Force
#InstallKeybdHook
#Persistent
#Requires AutoHotkey >=1.1.36 <1.9
Menu, Tray, Icon, icons\settingsIcon.ico
Process, Priority, , H
SetCapsLockState, AlwaysOff

; If (!A_IsAdmin){
; Run *RunAs "%A_AhkPath%" "%A_ScriptFullPath%"
; }

global tempFolderPath := A_ScriptDir . "\temp"

global stopwatchPID, timerPID, pomodoroPID, optionsPID
global stopwatchPIDFile := tempFolderPath . "\stopwatchPID.txt"
global timerPIDFile := tempFolderPath . "\timerPID.txt"
global pomodoroPIDFile := tempFolderPath . "\pomodoroPID.txt"
global optionsPIDFile := tempFolderPath . "\optionsPID.txt"

createAllTemp()





; ========= CAPS LOCK ============


~CapsLock::
sleep 500
SetCapsLockState, Off
return


RunStopwatch(argument=True) {

    if (getkeystate("alt") or getkeystate("shift")){
        SendCommand("pauseStopwatch", 65433)
        return
    }
    FileRead, stopwatchPID, %stopwatchPIDFile%
    ; msgbox %stopwatchPID%
    if (stopwatchPID) {
        Process, Exist, %stopwatchPID%
        pidExists := ErrorLevel
        Process, Exist, stopwatch.exe
        if (pidExists || ErrorLevel) {
            Process, Close, %stopwatchPID%
            Process, Close, stopwatch.exe
            ; stopwatchPID := ""  ; Сбросим ID после закрытия
            rewriteFile(stopwatchPIDFile,"")
            return
        }
    }
    argument := "stopwatch " . argument 
    pathToExe := A_ScriptDir . "\python\HustlerChronos.dist\HustlerChronos.exe" 
    pathToPython := A_ScriptDir . "\python\HustlerChronos.py" 

    ; Run, %pathToStopwatch% %argument%,, hide, stopwatchPID
    ; pathToStopwatch := A_ScriptDir . "\python\stopwatch.py" 
    ; Run, python.exe cmd /k %pathToStopwatch% %argument%,,, stopwatchPID
    

    if FileExist(pathToExe) {
        Run, %pathToExe% %argument% ,,hide, stopwatchPID
    } else if FileExist(pathToPython) {
            RunWait, python --version,, Hide, ErrorLevel
    
    if (ErrorLevel = 0) {
        Run, python.exe %pathToPython% %argument% ,,hide, stopwatchPID
    } else {
        MsgBox, 16, "Error, Python not found. Install Python or use compiled version."
    }
    } else {
       MsgBox, 16, "Error: Neither the EXE file nor the Python script was found"
    }


    rewriteFile(stopwatchPIDFile,stopwatchPID)
}



Capslock & Q::RunStopwatch("reset")
Capslock & W::RunStopwatch()




;;;;;;;


Capslock & A::
SetDefaultKeyboard(0x0409)
SendInput ^!+l
sleep 300
SetDefaultKeyboard(0x0419)
return

Capslock & S::
ProcessName := "Todoist.exe"
Process, Exist, %ProcessName%  ; Проверяем, запущен ли процесс
if (ErrorLevel = 0) {  
    Run, "todoist://" ; Укажите реальный путь к Todoist.exe
	return
}
SetDefaultKeyboard(0x0409)
SendInput ^!+m
; sleep 100
WinGet, activeprocess, ProcessName, A
WinGetTitle, windowTitle, A
if (InStr(activeprocess, "todoist") && windowTitle!="Inbox"){
Send g
Send i
}
SetDefaultKeyboard(0x0419)
return

Capslock & d:: 
Run, obsidian://daily
return

;;;;;;;



RunTimer(time) {
	if (getkeystate("alt") or getkeystate("shift")){
		SendCommand("pauseTimer", 65434)
		return
	}
	FileRead, timerPID, %timerPIDFile%
    if (timerPID) {
        Process, Exist, %timerPID%
        pidExists := ErrorLevel
        Process, Exist, timer.exe
        if (pidExists || ErrorLevel) {
            Process, Close, %timerPID%
            Process, Close, timer.exe
            timerPID := ""  ; Сброс ID после закрытия
			rewriteFile(timerPIDFile,"")
			return ; удалить ретурн если хочешь, чтобы таймер закрывался только той же кнопкой которой запускался, в других случаях переоткрывался новый
        }
    }
    argument := "timer " . time
    pathToExe := A_ScriptDir . "\python\HustlerChronos.dist\HustlerChronos.exe" 
    pathToPython := A_ScriptDir . "\python\HustlerChronos.py" 
    ; Run, %pathToStopwatch% %time%,, hide, timerPID
    ; Run, cmd /k %pathToStopwatch% %time%,, , timerPID

    if FileExist(pathToExe) {
        Run, %pathToExe% %argument% ,,hide, timerPID
    } else if FileExist(pathToPython) {
            RunWait, python --version,, Hide, ErrorLevel
    
    if (ErrorLevel = 0) {
        Run, python.exe %pathToPython% %argument% ,,hide, timerPID
    } else {
        MsgBox, 16, "Error, Python not found. Install Python or use compiled version."
    }
    } else {
       MsgBox, 16, "Error: Neither the EXE file nor the Python script was found"
    }
    
	rewriteFile(timerPIDFile,timerPID)
}


Capslock & 1::RunTimer(1)
Capslock & 2::RunTimer(3)
Capslock & 3::RunTimer(5)
Capslock & 4::RunTimer(10)
Capslock & 5::RunTimer(20)
Capslock & 6::RunTimer(30)
Capslock & 7::RunTimer(45)
Capslock & 8::RunTimer(60)
Capslock & 9::RunTimer(90)
Capslock & 0::RunTimer(120)




;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


RunPomodoro(args*){
    if (getkeystate("alt") or getkeystate("shift")){
        SendCommand("pausePomodoro", 65432)
        return
    }
    ; msgbox %args%
    list := []
    for index, value in args {
        ; msgbox %value%
        list.Push(value)
    }
    strList :=StrJoin(list, " ")
    FileRead, pomodoroPID, %pomodoroPIDFile%
    if (pomodoroPID) {
        Process, Exist, %pomodoroPID%
        pidExists := ErrorLevel
        Process, Exist, pomodoro.exe
        if (pidExists || ErrorLevel) {
            Process, Close, %pomodoroPID%
            Process, Close, pomodoro.exe
            pomodoroPID := ""  ; Сброс ID после закрытия
            rewriteFile(pomodoroPIDFile,"")
            return
        }
    }
    argument := "pomodoro " . strList
    pathToExe := A_ScriptDir . "\python\HustlerChronos.dist\HustlerChronos.exe" 
    pathToPython := A_ScriptDir . "\python\HustlerChronos.py" 
    if FileExist(pathToExe) {
        Run, %pathToExe% %argument% ,,hide, pomodoroPID
    
    } else if FileExist(pathToPython) {
            RunWait, python --version,, Hide, ErrorLevel
    
    if (ErrorLevel = 0) {
        Run, python.exe %pathToPython% %argument% ,,hide, pomodoroPID
    } else {
        MsgBox, 16, "Error, Python not found. Install Python or use compiled version."
    }
    } else {
       MsgBox, 16, "Error: Neither the EXE file nor the Python script was found"
    }
    
    rewriteFile(pomodoroPIDFile,pomodoroPID)
}


Capslock & z::RunPomodoro(true,5,1)
Capslock & x::RunPomodoro(true,25,5)
Capslock & c::RunPomodoro(true,55,5)
Capslock & v::RunPomodoro("custom")


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;




CapsLock & n::  ; отправляет команду пропуска круга
SendCommand("skipRest", 65432)
return


CapsLock & y::
FileRead, optionsPID, %optionsPIDFile%
if (optionsPID) {
    Process, Exist, %optionsPID%
    pidExists := ErrorLevel
    Process, Exist, options.exe
    
    if (pidExists || ErrorLevel) {
        Process, Close, %optionsPID%
        Process, Close, options.exe
		rewriteFile(optionsPIDFile,"")
		return
	}
}
pathToExe := A_ScriptDir . "\python\HustlerChronos.dist\HustlerChronos.exe" 
pathToPython := A_ScriptDir . "\python\HustlerChronos.py" 
; Run, %pathToOptions% "options",, hide,optionsPID

    if FileExist(pathToExe) {
        Run, %pathToExe% "options" ,,hide, optionsPID
    
    } else if FileExist(pathToPython) {
            RunWait, python --version,, Hide, ErrorLevel
    
    if (ErrorLevel = 0) {
        Run, python.exe %pathToPython% "options" ,,hide, optionsPID
    } else {
        MsgBox, 16, "Error, Python not found. Install Python or use compiled version."
    }
    } else {
       MsgBox, 16, "Error: Neither the EXE file nor the Python script was found"
    }

rewriteFile(optionsPIDFile, optionsPID)
return







;                    ;       FUNCTIONS       ;                    ;   


SetDefaultKeyboard(LocaleID){
	Static SPI_SETDEFAULTINPUTLANG := 0x005A, SPIF_SENDWININICHANGE := 2
	Lan := DllCall("LoadKeyboardLayout", "Str", Format("{:08x}", LocaleID), "Int", 0)
	VarSetCapacity(binaryLocaleID, 4, 0)
	NumPut(LocaleID, binaryLocaleID)
	DllCall("SystemParametersInfo", "UInt", SPI_SETDEFAULTINPUTLANG, "UInt", 0, "UPtr", &binaryLocaleID, "UInt", SPIF_SENDWININICHANGE)
	WinGet, windows, List
	Loop % windows {
		PostMessage 0x50, 0, % Lan, , % "ahk_id " windows%A_Index%
	}
}



rewriteFile(path,data){
file := FileOpen(path, "w")  ; "w" означает режим перезаписи
file.Write(data)
file.Close()
}


SendCommand(command, socket) {
    static AF_INET := 2, SOCK_STREAM := 1, IPPROTO_TCP := 6
    static INVALID_SOCKET := -1, SOCKET_ERROR := -1

    ; Загружаем библиотеку Winsock
    ws2_32 := DllCall("LoadLibrary", "Str", "ws2_32.dll", "Ptr")

    ; Инициализируем Winsock
    VarSetCapacity(WSAData, 32, 0)
    if (DllCall("ws2_32\WSAStartup", "UShort", 0x0202, "Ptr", &WSAData))
        return MsgBox, Ошибка WSAStartup!

    ; Создаём сокет
    sock := DllCall("ws2_32\socket", "Int", AF_INET, "Int", SOCK_STREAM, "Int", IPPROTO_TCP, "Int")
    if (sock = INVALID_SOCKET)
        return MsgBox, Ошибка создания сокета!

    ; Заполняем структуру sockaddr_in
    VarSetCapacity(addr, 16, 0)
    NumPut(AF_INET, addr, 0, "UShort")  ; Семейство адресов
    NumPut(DllCall("ws2_32\htons", "UShort", socket), addr, 2, "UShort")  ; Порт
    NumPut(DllCall("ws2_32\inet_addr", "AStr", "127.0.0.1"), addr, 4, "UInt")  ; IP

    ; Подключаемся к серверу
    if (DllCall("ws2_32\connect", "Int", sock, "Ptr", &addr, "Int", 16) = SOCKET_ERROR) {
        DllCall("ws2_32\closesocket", "Int", sock)
        return MsgBox, Ошибка соединения с сервером!
    }

    ; Отправляем команду
    DllCall("ws2_32\send", "Int", sock, "AStr", command, "Int", StrLen(command), "Int", 0)

    ; Закрываем соединение
    DllCall("ws2_32\closesocket", "Int", sock)
    DllCall("ws2_32\WSACleanup")

    ; Освобождаем библиотеку Winsock
    DllCall("FreeLibrary", "Ptr", ws2_32)
}


StrJoin(arr, sep := ", ") {
    str := ""
    for i, val in arr
        str .= (i = 1 ? "" : sep) val
    return str
}


createAllTemp(){
    if !FileExist(tempFolderPath) {
        FileCreateDir, %tempFolderPath%
    } 
    if !FileExist(stopwatchPIDFile) {
        rewriteFile(stopwatchPIDFile,stopwatchPID)
    } 
    if !FileExist(timerPIDFile) {
        ; FileCreateDir, %timerPIDFile%
        rewriteFile(timerPIDFile,timerPID)
    } 
    if !FileExist(pomodoroPIDFile) {
        ; FileCreateDir, %pomodoroPIDFile%
        rewriteFile(pomodoroPIDFile,pomodoroPID)
    } 
    if !FileExist(optionsPIDFile) {
        ; FileCreateDir, %optionsPIDFile%
        rewriteFile(optionsPIDFile,optionsPID)
    }     

}
