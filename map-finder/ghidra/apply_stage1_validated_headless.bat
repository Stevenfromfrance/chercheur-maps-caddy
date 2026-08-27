@echo off
REM Apply Stage1 validated labels headless on PCR21_Golf9980.
REM Close Ghidra GUI first if PCR21_Golf9980.lock exists.
setlocal
set "GHIDRA_HOME=C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC"
set "JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
if exist "%JAVA_HOME%\bin\java.exe" set "PATH=%JAVA_HOME%\bin;%PATH%"
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PROJECT_DIR=C:\Users\theda\Tools\ghidra-projects"
set "PROJECT_NAME=PCR21_Golf9980"
set "BIN_NAME=Golf6_03L997558A_9980_FULLFLASH.bin"
set "SCRIPTS_SYNC=C:\Users\theda\ghidra_scripts"

REM Prefer synced scripts folder (CSV + NameHubStage1Validated.py)
set "SPATH=%SCRIPTS_SYNC%"
if not exist "%SPATH%\NameHubStage1Validated.py" set "SPATH=%SCRIPT_DIR%"
if not exist "%SPATH%\golf9980_stage1_validated.csv" (
  echo ERROR: golf9980_stage1_validated.csv missing in %SPATH%
  echo Run: python map-finder\ghidra\identify_atlas_starts.py
  echo      python map-finder\ghidra\build_stage1_validated_pack.py
  exit /b 1
)

if exist "%PROJECT_DIR%\%PROJECT_NAME%.lock" (
  echo WARN: project lock present - close Ghidra GUI then re-run.
  exit /b 2
)

REM Keep ghidra_scripts in sync with this folder (CSV + new postScripts).
copy /Y "%SCRIPT_DIR%\KickFromCallSites.py" "%SPATH%\KickFromCallSites.py" >nul
copy /Y "%SCRIPT_DIR%\KickParents.py" "%SPATH%\KickParents.py" >nul
copy /Y "%SCRIPT_DIR%\DumpStage1Xrefs.py" "%SPATH%\DumpStage1Xrefs.py" >nul
copy /Y "%SCRIPT_DIR%\NameHubStage1Validated.py" "%SPATH%\NameHubStage1Validated.py" >nul
copy /Y "%SCRIPT_DIR%\NameInterpFamilies.py" "%SPATH%\NameInterpFamilies.py" >nul
if exist "%SCRIPT_DIR%\golf9980_parent_seeds.txt" copy /Y "%SCRIPT_DIR%\golf9980_parent_seeds.txt" "%SPATH%\golf9980_parent_seeds.txt" >nul

echo Applying labels + interp families + kick call-sites + parents + XREF dump...
call "%GHIDRA_HOME%\support\analyzeHeadless.bat" "%PROJECT_DIR%" %PROJECT_NAME% -process "%BIN_NAME%" -noanalysis -scriptPath "%SPATH%" -postScript NameHubStage1Validated.py -postScript NameInterpFamilies.py -postScript KickFromCallSites.py -postScript KickParents.py -postScript DumpStage1Xrefs.py
set "RC=%ERRORLEVEL%"
echo analyzeHeadless exit=%RC%
endlocal & exit /b %RC%
