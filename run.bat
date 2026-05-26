@echo off
echo ===================================================
echo   Starting Madridista Central Setup and Server
echo ===================================================
echo.

echo [1/3] Installing Python dependencies...
python -m pip install requests beautifulsoup4
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Failed to install Python dependencies automatically. 
    echo Please make sure Python is installed and added to your PATH.
    pause
    exit /b
)

echo.
echo [2/3] Running scraper for the first time to generate news.json...
python scraper.py
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Failed to run scraper. News page will load with fallback data.
)

echo.
echo [3/3] Starting local HTTP Web Server...
echo.
echo ---------------------------------------------------
echo   WEBSITE IS RUNNING!
echo   Open your browser and go to: http://localhost:8000
echo ---------------------------------------------------
echo.
echo To stop the server and scraper, close this command window.
echo.

python -m http.server 8000
