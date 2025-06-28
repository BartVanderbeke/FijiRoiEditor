@echo off
REM ------------------------------------------------------------
REM Standalone launcher for Edit_Rois.py
REM Works independently from Fiji GUI
REM ------------------------------------------------------------

set "FIJI_DIR="
set "CLASSPATH="
echo [1/4] Searching for Fiji executable
echo [1/4] checking current folder
if exist ".\fiji-windows-x64.exe" (
    set "FIJI_DIR=%CD%\"
    goto :Fiji_found
)
echo [1/4] checking C: drive, this may take a while
for /f "delims=" %%A in ('dir "C:\fiji-windows-x64.exe" /s /b 2^>nul') do (
    set "FIJI_DIR=%%~dpA"
    goto :Fiji_found
)

echo [1/4] [ERROR] Fiji executable not found.
pause
exit /b 1

:Fiji_found
echo [1/4] [OK] Fiji executable found in %FIJI_DIR%

echo [2/4] Build classpath for Jython
set CLASSPATH=%FIJI_DIR%\jars\*;%FIJI_DIR%\plugins\*;%FIJI_DIR%\jars\lib\*
echo [2/4] Set class path to %CLASSPATH%

echo [3/4] Launch Jython on Java virtual machine
echo [3/4] Finding Java JVM
for /f "delims=" %%P in ('where java.exe 2^>nul') do (
    goto :found_java
)
echo [3/4] [ERROR] Java not found
pause
exit /b

:found_java
echo [4/4] [OK] Java found, starting app
java --enable-native-access=ALL-UNNAMED -cp "%CLASSPATH%" org.python.util.jython %FIJI_DIR%\plugins\Edit_Rois.py

pause
