@echo off
echo ====================================
echo FinBuddy Setup
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
    echo "Creating .env file..."

    # -- AI Config --
    echo "GROQ_API_KEY=your_key" > .env
    echo "GROQ_MODEL_NAME=ai_model" >> .env

    # -- App Security --
    echo "SECRET_KEY=secret_key" >> .env
    echo "DATABASE_URL=your_database" >> .env

    # -- Mail Settings --
    echo "" >> .env
    echo "# Mail settings for weekly reports" >> .env
    echo "MAIL_SERVER=smtp.gmail.com" >> .env
    echo "MAIL_PORT=587" >> .env
    echo "MAIL_USE_TLS=true" >> .env
    echo "MAIL_USE_SSL=false" >> .env
    echo "MAIL_USERNAME=email" >> .env
    echo "MAIL_PASSWORD=password" >> .env
    echo "MAIL_DEFAULT_SENDER=email" >> .env

    # -- Scheduler Settings --
    echo "" >> .env
    echo "# Weekly report scheduler" >> .env
    echo "ENABLE_WEEKLY_REPORTS=true" >> .env
    echo "WEEKLY_REPORT_DAY=sun" >> .env
    echo "WEEKLY_REPORT_HOUR=8" >> .env

    # -- Tuition Settings --
    echo "" >> .env
    echo "# Tuition reminders (email)" >> .env
    echo "ENABLE_TUITION_REMINDERS=true" >> .env

    echo ".env file created successfully."
    
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
echo   2. Run: python migrate_all.py
echo   3. Run: python app.py
echo.
echo The application will be available at http://localhost:5000
echo.
pause
