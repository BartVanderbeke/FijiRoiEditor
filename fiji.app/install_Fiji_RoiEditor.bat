@echo off
setlocal EnableDelayedExpansion

echo [1/6] Determine Fiji base directory
set "FIJI_EXE="

echo [1/6] Searching for Fiji executable
for /f "delims=" %%A in ('dir "C:\fiji-windows-x64.exe" /s /b') do (
    set "FIJI_EXE=%%A"
    goto :Fiji_found
)

echo [1/6] [ERROR] Fiji not found, please install Fiji first
pause
exit /b

:Fiji_found
echo [1/6] [OK] Found Fiji: !FIJI_EXE!

:: extract FIJI_DIR from FIJI_EXE
for %%F in ("!FIJI_EXE!") do set "FIJI_DIR=%%~dpF"
:: remove trailing backslash if present
if "!FIJI_DIR:~-1!"=="\" set "FIJI_DIR=!FIJI_DIR:~0,-1!"

echo [2/6] Looking for jars in !FIJI_DIR!\jars
set "JYTHON_JAR="
for %%J in ("!FIJI_DIR!\jars\jython-*.jar") do (
    set "JYTHON_JAR=%%J"
    goto :jython_found
)

echo [2/6] [ERROR] Jython jar not found, something's wrong with your Fiji installation
pause
exit /b

:jython_found
echo [2/6] [OK] Found Jython jar in: !JYTHON_JAR!

echo [3/6] Copy plugins folder
:: copy \plugins\ subfolder of current folder to FIJI_DIR\plugins
xcopy ".\plugins\*.py" "!FIJI_DIR!\plugins" /E /Y /I

echo [4/6] Copy jars\lib folder
:: copy \jars\lib subfolder of current folder to FIJI_DIR\jars\lib
xcopy ".\jars\lib\*.py" "!FIJI_DIR!\jars\lib" /E /Y /I

echo [5/6] Copy assets folder
:: copy \assets subfolder of current folder to FIJI_DIR\assets (create if not exists)
if not exist "!FIJI_DIR!\assets" mkdir "!FIJI_DIR!\assets"
xcopy ".\assets\*.ico" "!FIJI_DIR!\assets" /E /Y /I

echo [6/6] Copy content of current folder to FIJI_DIR
:: copy current folder content to FIJI_DIR (non-recursive)
xcopy ".\*.bat" "!FIJI_DIR!\" /Y

:: Create desktop shortcut
powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'FijiRoiEditor.lnk')); " ^
 "$s.TargetPath = 'start_Roi_Editor.bat'; " ^
 "$s.Arguments = ''; " ^
 "$s.WorkingDirectory = $env:USERPROFILE; " ^
 "$s.IconLocation = '%~dp0assets\FijiRoiEditor.ico'; " ^
 "$s.Save()"

echo [6/6] Created FijiRoiEditor shortcut on desktop

endlocal
cmd /k
exit /b
