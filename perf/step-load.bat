@echo off
chcp 65001 >nul
cd /d "%~dp0"

if "%JMETER_HOME%"=="" set "JMETER_HOME=D:\AIBase\测试作业\tools\apache-jmeter-5.6.3"
if not exist "%JMETER_HOME%\bin\jmeter.bat" (
    echo [ERROR] 未找到 JMeter：%JMETER_HOME%
    exit /b 1
)

if not exist "results" mkdir "results"

for %%n in (10 20 50 100 200) do (
    echo.
    echo ===== 阶梯加压：%%n 线程 / 5 分钟 =====
    if exist "results\html-step-%%n" rmdir /s /q "results\html-step-%%n"
    if exist "results\step-%%n.jtl" del /q "results\step-%%n.jtl"
    call "%JMETER_HOME%\bin\jmeter.bat" -n -t scenario-query.jmx ^
      -l "results\step-%%n.jtl" ^
      -j "results\step-%%n.log" ^
      -e -o "results\html-step-%%n" ^
      -Jthreads=%%n -Jramp=5 -Jduration=300 -Jport=8080 ^
      -Jsampleresult.default.encoding=UTF-8
)

python summarize_step_load.py
python plot_step_load.py
echo.
echo 完成：results\step-load-summary.csv / step-load-summary.md / html-step-*
