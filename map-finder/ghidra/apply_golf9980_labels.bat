@echo off
setlocal
set "GHIDRA_HOME=C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC"
set "JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
call "%GHIDRA_HOME%\support\analyzeHeadless.bat" "C:\Users\theda\Tools\ghidra-projects" PCR21_Golf9980 -process Golf6_03L997558A_9980_FULLFLASH.bin -noanalysis -scriptPath "%SCRIPT_DIR%" -postScript ImportAtlas_Golf9980.py
endlocal
