@echo off
cls

echo ================================================
echo    达丹科技 - 潜意识音频生成器 (Web版)
echo ================================================
echo.
echo 正在启动Web服务器...
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境，请先安装Python。
    echo 可以从 https://www.python.org/downloads/ 下载并安装。
    echo.
    pause
    exit /b 1
)

:: 启动Web应用
echo 启动成功！
echo.
echo 请在浏览器中打开: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo.
echo ================================================
echo.

python subliminal_maker_web.py

pause
