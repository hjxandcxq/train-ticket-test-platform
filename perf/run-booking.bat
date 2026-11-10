@echo off
chcp 65001 >nul
setlocal
rem 用法：run-booking.bat [并发线程数] [端口]
rem 例：run-booking.bat 10 8080

if "%JMETER_HOME%"=="" set "JMETER_HOME=D:\AIBase\测试作业\tools\apache-jmeter-5.6.3"
set BOOK_THREADS=%1
if "%BOOK_THREADS%"=="" set BOOK_THREADS=10
set PORT=%2
if "%PORT%"=="" set PORT=8080

if not exist "%JMETER_HOME%\bin\jmeter.bat" (
    echo [ERROR] 未找到 JMeter：%JMETER_HOME%
    exit /b 1
)

if not exist "%~dp0results" mkdir "%~dp0results"
if exist "%~dp0results\html-book" rmdir /s /q "%~dp0results\html-book"
if exist "%~dp0results\book-%BOOK_THREADS%.jtl" del /q "%~dp0results\book-%BOOK_THREADS%.jtl"

echo 运行并发下单：线程=%BOOK_THREADS% 端口=%PORT%
echo 提示：先执行 00_perf_seed.sql（或 01_perf_reset.sql）复位余票，压测后查库核对库存与订单数
"%JMETER_HOME%\bin\jmeter.bat" -n -t "%~dp0booking-concurrency.jmx" ^
  -l "%~dp0results\book-%BOOK_THREADS%.jtl" ^
  -j "%~dp0results\book-%BOOK_THREADS%.log" ^
  -e -o "%~dp0results\html-book" ^
  -JbookThreads=%BOOK_THREADS% -Jport=%PORT% ^
  -Jsampleresult.default.encoding=UTF-8
endlocal
