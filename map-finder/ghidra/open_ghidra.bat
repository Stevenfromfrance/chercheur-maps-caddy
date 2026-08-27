@echo off
setlocal
set "JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
start "" "C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC\ghidraRun.bat"
echo Ghidra starting.
echo Project Golf 9980 full flash: C:\Users\theda\Tools\ghidra-projects\PCR21_Golf9980
echo Project Caddy cal-only:       C:\Users\theda\Tools\ghidra-projects\PCR21
endlocal
