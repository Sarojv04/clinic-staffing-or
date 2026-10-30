@echo off
cd /d "%~dp0"
pip install -r requirements.txt
python src\run_all.py
echo.
echo Done. Open the outputs folder to see the charts.
pause
