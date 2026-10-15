@echo off
chcp 65001 >nul
echo =============================================
echo   中国美术史课程大纲更新工具 — 安装依赖
echo =============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python。
    echo 请先安装 Python：https://www.python.org/downloads/
    echo 安装时务必勾选 "Add Python to PATH"。
    pause
    exit /b 1
)

echo 正在安装 Python 依赖库，请稍候...
echo.
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 安装过程中出现问题，请检查网络连接后重试。
    pause
    exit /b 1
)

echo.
echo =============================================
echo   安装完成！
echo =============================================
echo.
echo 接下来请安装字体：
echo 打开 fonts\ 文件夹，全选所有字体文件，
echo 右键选择"为所有用户安装"。
echo.
pause
