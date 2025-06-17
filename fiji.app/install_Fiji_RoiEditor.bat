@echo off
setlocal EnableDelayedExpansion

echo [1/7] Determine Fiji base directory
set "FIJI_EXE="

echo [1/7] Searching for Fiji executable, this may take a while
for /f "delims=" %%A in ('dir "C:\fiji-windows-x64.exe" /s /b') do (
    set "FIJI_EXE=%%A"
    goto :Fiji_found
)

echo [1/7] [ERROR] Fiji not found, please install Fiji first
pause
exit /b

:Fiji_found
echo [1/7] [OK] Found Fiji: !FIJI_EXE!

:: extract FIJI_DIR from FIJI_EXE
for %%F in ("!FIJI_EXE!") do set "FIJI_DIR=%%~dpF"
:: remove trailing backslash if present
if "!FIJI_DIR:~-1!"=="\" set "FIJI_DIR=!FIJI_DIR:~0,-1!"

echo [2/7] Looking for jars in !FIJI_DIR!\jars
set "JYTHON_JAR="
for %%J in ("!FIJI_DIR!\jars\jython-*.jar") do (
    set "JYTHON_JAR=%%J"
    goto :jython_found
)

echo [2/7] [ERROR] Jython jar not found, something's wrong with your Fiji installation
pause
exit /b

:jython_found
echo [2/7] [OK] Found Jython jar in: !JYTHON_JAR!

echo [3/7] Copy plugins folder
:: copy \plugins\ subfolder of current folder to FIJI_DIR\plugins
xcopy ".\plugins\*.py" "!FIJI_DIR!\plugins" /E /Y /I

echo [4/7] Copy jars\lib folder
:: copy \jars\lib subfolder of current folder to FIJI_DIR\jars\lib
xcopy ".\jars\lib\*.py" "!FIJI_DIR!\jars\lib" /E /Y /I

echo [5/7] Copy assets folder
:: copy \assets subfolder of current folder to FIJI_DIR\assets (create if not exists)
if not exist "!FIJI_DIR!\assets" mkdir "!FIJI_DIR!\assets"
xcopy ".\assets\*.ico" "!FIJI_DIR!\assets" /E /Y /I

echo [6/7] Copy content of current folder to FIJI_DIR
:: copy current folder content to FIJI_DIR (non-recursive)
xcopy ".\start_Roi_Editor.bat" "!FIJI_DIR!\" /Y

echo [7/7]  Create desktop shortcut
powershell -NoProfile -Command ^
 "$fiji = '!FIJI_DIR!\';"  ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'FijiRoiEditor.lnk')); " ^
 "$s.TargetPath = '!FIJI_DIR!\start_Roi_Editor.bat'; " ^
 "$s.Arguments = ''; " ^
 "$s.WorkingDirectory = $fiji; " ^
 "$s.IconLocation = '%~dp0assets\FijiRoiEditor.ico'; " ^
 "$s.Save()"

echo [7/7] Created FijiRoiEditor shortcut on desktop

endlocal
cmd /k
exit /b
