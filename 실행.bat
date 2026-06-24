@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 활동 트래커를 시작합니다...
pip install -r requirements.txt >nul 2>&1
streamlit run app.py
pause
