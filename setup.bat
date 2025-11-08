@echo off
REM FiveM Webhook Manager - Quick Setup Script (Windows)

echo ==========================================
echo FiveM Webhook Manager v6.0 - Setup
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python not found. Please install Python 3.7 or higher.
    pause
    exit /b 1
)
python --version
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo X Failed to install dependencies
    pause
    exit /b 1
)
echo. Dependencies installed successfully
echo.

REM Create .env if not exists
if not exist .env (
    echo Creating .env file...
    copy .env.example .env >nul
    echo. Created .env file
    echo.
    echo WARNING: Edit .env and add your:
    echo    - Discord Bot Token
    echo    - Discord Guild ID  
    echo    - FiveM Resources Path
    echo.
) else (
    echo. .env file already exists
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env with your configuration
echo 2. Run in dry-run mode first:
echo    python fivem_webhook_manager.py
echo 3. Review the output
echo 4. Set DRY_RUN=false in .env
echo 5. Run for real!
echo.
echo For help, check README.md
echo.
pause
