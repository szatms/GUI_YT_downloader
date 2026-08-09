@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo Starting YouTube Downloader GUI...
python youtube_downloader_gui.py

echo.
echo Download complete. Press any key to exit.
pause