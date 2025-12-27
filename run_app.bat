@echo off
call .venv\Scripts\activate.bat
python migrate_all.py
python app.py
