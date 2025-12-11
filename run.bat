@echo off
cd /d "%~dp0"
echo Starting Saftrade...
poetry run python main.py
echo Done.
