@echo off
chcp 65001 > nul
title Boutique Carlo Acutis Foundation - Cahier Journal
echo =====================================================================
echo    BOUTIQUE CARLO ACUTIS FOUNDATION - CAHIER JOURNAL DE CAISSE
echo =====================================================================
echo.
echo Initialisation et verification de la base de donnees...
python database.py
echo.
echo Lancement du serveur Web Python (FastAPI / Uvicorn)...
echo Accessible sur : http://localhost:8000
echo.
start http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
