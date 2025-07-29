@echo off
REM Tissue Installation Script for Windows
REM This script ensures a clean installation without package conflicts

echo 🩹 Tissue Installation Script (Windows)
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not found
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment
echo 📦 Creating virtual environment...
if exist venv (
    echo ⚠️  Removing existing venv directory
    rmdir /s /q venv
)

python -m venv venv

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Remove any conflicting packages
echo 🧹 Removing any conflicting 'github' packages...
pip uninstall -y github 2>nul
pip uninstall -y PyGithub 2>nul

REM Install core dependencies explicitly
echo 📦 Installing core dependencies...
pip install "PyGithub>=1.58.0"
pip install "click>=8.0.0"
pip install "pandas>=1.5.0"

REM Install development dependencies
echo 🔧 Installing development dependencies...
pip install "pytest>=7.0.0"
pip install "pytest-cov>=4.0.0"

REM Install the package in development mode
echo 🔨 Installing Tissue in development mode...
pip install -e .

REM Force reinstall to ensure console scripts are updated
echo 🔄 Updating console scripts...
pip install --force-reinstall --no-deps -e .

REM Verify installation
echo ✅ Verifying installation...
python -c "try: from github import Github, GithubException; print('✅ PyGithub imported successfully'); from src.csv_parser import CSVParser; print('✅ CSV Parser imported successfully'); from src.github_client import GitHubClient; print('✅ GitHub Client imported successfully'); print('✅ All core modules imported successfully') except ImportError as e: print(f'❌ Import failed: {e}'); exit(1)"

REM Test CLI command
echo 🧪 Testing CLI command...
python -m src.main --help >nul 2>&1
if errorlevel 1 (
    tissue --help >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  CLI commands need troubleshooting, but core install is complete
    ) else (
        echo ✅ tissue command works!
    )
) else (
    echo ✅ CLI module works!
)

echo.
echo 🎉 Installation completed successfully!
echo.
echo To activate the environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To use tissue, try either:
echo   tissue --help                # If tissue command is in PATH  
echo   python -m src.main --help    # Alternative method
echo.
echo Example usage:
echo   tissue --file issues.csv --repo owner/repo --token ghp_xxx

pause
