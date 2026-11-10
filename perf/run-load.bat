@echo off
chcp 65001 >nul
setlocal
rem 用法：run-load.bat [线程数] [ramp秒] [循环次数] [端口]
rem 例：run-load.bat 50 10 10 8080

if "%JMETER_HOME%"=="" set "JMETER_HOME=D:\AIBase\测试作业\tools\apache-jmeter-5.6.3"
set THREADS=%1
if "%THREADS%"=="" set THREADS=10
set RAMP=%2
if "%RAMP%"=="" set RAMP=5
set LOOPS=%3
if "%LOOPS%"=="" set LOOPS=10
set PORT=%4
if "%PORT%"=="" set PORT=8080

if not exist "%JMETER_HOME%\bin\jmeter.bat" (
    echo [ERROR] 未找到 JMeter：%JMETER_HOME%
    exit /b 1
)

if not exist "%~dp0results" mkdir "%~dp0results"
if exist "%~dp0results\html-%THREADS%" rmdir /s /q "%~dp0results\html-%THREADS%"
if exist "%~dp0results\load-%THREADS%.jtl" del /q "%~dp0results\load-%THREADS%.jtl"

echo 运行负载测试：线程=%THREADS% ramp=%RAMP%s loops=%LOOPS% 端口=%PORT%
"%JMETER_HOME%\bin\jmeter.bat" -n -t "%~dp0load-test.jmx" ^
  -l "%~dp0results\load-%THREADS%.jtl" ^
  -j "%~dp0results\load-%THREADS%.log" ^
  -e -o "%~dp0results\html-%THREADS%" ^
  -Jthreads=%THREADS% -Jramp=%RAMP% -Jloops=%LOOPS% -Jport=%PORT% ^
  -Jsampleresult.default.encoding=UTF-8
endlocal
