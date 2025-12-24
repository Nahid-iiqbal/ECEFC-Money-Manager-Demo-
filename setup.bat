@echo off
echo ====================================
echo ECEFC Money Manager Setup
echo ====================================
echo.

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    echo Please make sure Python is installed and added to PATH
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo [2/5] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated!
echo.

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo [4/5] Setting up environment file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo .env file created from template
        echo IMPORTANT: Please edit .env and set your SECRET_KEY
    ) else (
        echo Warning: .env.example not found, creating basic .env
        echo SECRET_KEY=change-this-to-a-random-secret-key> .env
        echo DATABASE_URL=sqlite:///finance.db>> .env
    )
) else (
    echo .env file already exists, skipping...
)
echo.

echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To start the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: python app.py
echo.
echo The application will be available at http://localhost:5000
echo.
pause
