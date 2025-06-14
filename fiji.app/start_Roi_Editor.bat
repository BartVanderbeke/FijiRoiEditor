@echo off
REM ------------------------------------------------------------
REM Standalone launcher for Edit_Rois.py
REM Works independently from Fiji GUI
REM ------------------------------------------------------------

echo [1/4] Searching for Fiji executable
for /f "delims=" %%A in ('dir ".\fiji-windows-x64.exe" /s /b') do (
    set "FIJI_EXE=%%A"
    goto :Fiji_found
)
echo [1/4] [ERROR] Fiji not found in current folder, please install Fiji first
pause
exit /b

:Fiji_found
echo [1/4] [OK] Fiji executable found

echo [2/4] Build classpath for Jython
set CLASSPATH=.\jars\*;.\plugins\*
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
java --enable-native-access=ALL-UNNAMED -cp "%CLASSPATH%" org.python.util.jython Edit_Rois.py

pause
