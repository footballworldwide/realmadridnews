@echo off
echo ===================================================
echo       AI Pulse - Setup and Local Server
echo ===================================================
echo.

echo [1/3] Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Failed to install Python dependencies.
    echo Please make sure Python is installed and added to PATH.
    pause
    exit /b
)

echo.
echo [2/3] Running AI news scraper...
python scraper.py
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Scraper failed. Site will load with fallback data.
)

echo.
echo [3/3] Starting local HTTP Web Server...
echo.
echo ---------------------------------------------------
echo   AI PULSE IS RUNNING!
echo   Open your browser: http://localhost:8000
echo ---------------------------------------------------
echo.
echo To stop the server, close this window.
echo.

python -m http.server 8000
