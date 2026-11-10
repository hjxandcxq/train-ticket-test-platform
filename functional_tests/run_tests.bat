@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "..\.venv-tests\Scripts\python.exe" (
    echo [ERROR] 未找到 .venv-tests，请先在项目根目录创建虚拟环境并安装依赖：
    echo   python -m venv .venv-tests
    echo   .venv-tests\Scripts\python.exe -m pip install -r functional_tests\requirements.txt
    exit /b 1
)

"..\.venv-tests\Scripts\python.exe" -m pytest -v --html=report.html --self-contained-html
