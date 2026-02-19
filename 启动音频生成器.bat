@echo off
cls

echo ================================
echo 达丹科技 - 潜意识音频生成器
echo ================================
echo 正在启动...
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

echo Python环境正常，启动应用...
echo.

:: 启动Python脚本
python subliminal_maker.py

:: 检查脚本运行结果
if %errorlevel% neq 0 (
    echo.
    echo 应用程序遇到错误，请查看上面的错误信息。
    echo.
    pause
    exit /b 1
)

echo.
echo 应用程序已退出。
pause
