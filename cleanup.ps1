# Cleanup script for NewsHub project

# Remove Python cache directories
Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*/__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# Remove Python compiled files
Remove-Item -Path "*.pyc" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*.pyc" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*/*.pyc" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.pyo" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*.pyo" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*/*.pyo" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.pyd" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*.pyd" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/*/*.pyd" -Recurse -Force -ErrorAction SilentlyContinue

# Remove virtual environment
if (Test-Path -Path "venv") {
    Remove-Item -Path "venv" -Recurse -Force
}
if (Test-Path -Path "myenv") {
    Remove-Item -Path "myenv" -Recurse -Force
}

# Remove IDE specific files
Remove-Item -Path ".vscode" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".idea" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.sublime-workspace" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.sublime-project" -Force -ErrorAction SilentlyContinue

# Remove distribution / packaging directories
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue

# Remove testing and coverage files
Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".mypy_cache" -Recurse -Force -ErrorAction SilentlyContinue

# Remove Jupyter notebook checkpoints
Remove-Item -Path ".ipynb_checkpoints" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*/.ipynb_checkpoints" -Recurse -Force -ErrorAction SilentlyContinue

# Remove local development database
Remove-Item -Path "db.sqlite3" -Force -ErrorAction SilentlyContinue

# Remove Python cache directories (alternative patterns)
Get-ChildItem -Directory -Recurse -Force -Include "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -File -Recurse -Force -Include "*.py[co]" | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup completed successfully!" -ForegroundColor Green
