@echo off
title Leads AI Agent - Google Maps Outreach
echo ===================================================
echo     STARTING LEADS AI AGENT (GOOGLE MAPS HUNTER)
echo ===================================================
echo.

cd /d "%~dp0"
python -m streamlit run app.py

pause
