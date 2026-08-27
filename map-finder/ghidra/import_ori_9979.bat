@echo off
REM PCR2.1 — import ORI 9979 into Ghidra (no flash). Labels from atlas.
setlocal
set "GHIDRA_HOME=C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC"
set "JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
if not exist "%JAVA_HOME%\bin\java.exe" (
  for /d %%D in ("C:\Program Files\Microsoft\jdk-21*") do set "JAVA_HOME=%%D"
)
set "PATH=%JAVA_HOME%\bin;%PATH%"

set "PROJECT_DIR=C:\Users\theda\Tools\ghidra-projects"
set "PROJECT_NAME=PCR21"
set "ORI=C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules\Caddy-CAYE-2013-03L906023PA-2531\ORI\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if not exist "%GHIDRA_HOME%\support\analyzeHeadless.bat" (
  echo Ghidra not found at %GHIDRA_HOME%
  exit /b 1
)
if not exist "%ORI%" (
  echo ORI not found: %ORI%
  exit /b 1
)
if not exist "%PROJECT_DIR%" mkdir "%PROJECT_DIR%"

echo JAVA_HOME=%JAVA_HOME%
"%JAVA_HOME%\bin\java.exe" -version
echo Importing ORI into Ghidra project %PROJECT_NAME% ...
echo Base 0xA0000000  language tricore:LE:32:tc176x  NO full auto-analysis

call "%GHIDRA_HOME%\support\analyzeHeadless.bat" "%PROJECT_DIR%" %PROJECT_NAME% -import "%ORI%" -processor tricore:LE:32:tc176x -cspec default -loader BinaryLoader -loader-baseAddr 0xa0000000 -overwrite -noanalysis -scriptPath "%SCRIPT_DIR%" -postScript ImportAtlas_9979.py

echo.
echo Open GUI: %GHIDRA_HOME%\ghidraRun.bat
echo Project : %PROJECT_DIR%\%PROJECT_NAME%.gpr
echo Then: File ^> Open ^> PCR21 ^> the imported program
echo Search labels: G  then type AccPed_trq4A or tqlim_cluth_prot
endlocal
