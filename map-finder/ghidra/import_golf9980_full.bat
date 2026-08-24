@echo off
REM Import Golf 9980 FULL FLASH (code+cal) into Ghidra. Analysis of bin only, no flash.
setlocal
set "GHIDRA_HOME=C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC"
set "JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
if not exist "%JAVA_HOME%\bin\java.exe" (
  for /d %%D in ("C:\Program Files\Microsoft\jdk-21*") do set "JAVA_HOME=%%D"
)
set "PATH=%JAVA_HOME%\bin;%PATH%"

set "PROJECT_DIR=C:\Users\theda\Tools\ghidra-projects"
set "PROJECT_NAME=PCR21_Golf9980"
set "BIN=C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin"
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if not exist "%BIN%" (
  echo Missing full flash bin: %BIN%
  exit /b 1
)
if not exist "%PROJECT_DIR%" mkdir "%PROJECT_DIR%"

echo Import Golf 9980 full flash - tricore tc176x @ 0x80000000 (uncached PFLASH)
call "%GHIDRA_HOME%\support\analyzeHeadless.bat" "%PROJECT_DIR%" %PROJECT_NAME% -import "%BIN%" -processor tricore:LE:32:tc176x -cspec default -loader BinaryLoader -loader-baseAddr 0x80000000 -overwrite -noanalysis -scriptPath "%SCRIPT_DIR%" -postScript ImportAtlas_Golf9980.py -postScript KickGolf9980.py

echo.
echo Open: map-finder\ghidra\open_ghidra.bat
echo Project: %PROJECT_DIR%\%PROJECT_NAME%.gpr
echo G then tqlim_cluth_prot  /  AccPed_trq4A  (addresses 0x801xxxxx)
echo Then Analysis Auto Analyze if you want more functions
endlocal
