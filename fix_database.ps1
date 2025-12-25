# Stop any running Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Stopped Python processes"

Start-Sleep -Seconds 2

# Delete the database file
Remove-Item "instance\database.db" -Force -ErrorAction SilentlyContinue
Write-Host "Deleted old database"

# Recreate the database
python reset_db.py

Write-Host "`nDatabase reset complete! You can now run: python app.py"
