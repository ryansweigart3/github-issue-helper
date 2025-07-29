#!/usr/bin/env python3
"""
Installation checker for Tissue
Run this script to verify all dependencies are correctly installed
"""

import sys
import subprocess

def check_package(package_name, import_name=None):
    """Check if a package is installed and can be imported"""
    if import_name is None:
        import_name = package_name
    
    print(f"Checking {package_name}...", end=" ")
    
    try:
        __import__(import_name)
        print("✅ OK")
        return True
    except ImportError as e:
        print(f"❌ FAILED - {e}")
        return False

def check_github_package():
    """Special check for PyGithub vs github package conflict"""
    print("Checking PyGithub installation...", end=" ")
    
    try:
        import github
        # Try to import the specific classes we need
        from github import Github, GithubException
        print("✅ OK")
        return True
    except ImportError as e:
        print(f"❌ FAILED - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED - Wrong 'github' package installed: {e}")
        print("  → Please run: pip uninstall github && pip install PyGithub")
        return False

def get_package_info(package_name):
    """Get information about installed package"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except:
        return None

def main():
    print("🔍 Tissue Installation Checker")
    print("=" * 40)
    
    all_good = True
    
    # Check core dependencies
    dependencies = [
        ("pandas", "pandas"),
        ("click", "click"),
    ]
    
    for package_name, import_name in dependencies:
        if not check_package(package_name, import_name):
            all_good = False
    
    # Special check for PyGithub
    if not check_github_package():
        all_good = False
        print("\n🛠️  To fix PyGithub issue:")
        print("   pip uninstall github")
        print("   pip install PyGithub")
    
    # Check optional development dependencies
    print("\nOptional dependencies:")
    dev_deps = [
        ("pytest", "pytest"),
        ("black", "black"),
        ("flake8", "flake8"),
    ]
    
    for package_name, import_name in dev_deps:
        check_package(package_name, import_name)
    
    print("\n" + "=" * 40)
    
    if all_good:
        print("🎉 All core dependencies are correctly installed!")
        print("You can now run: tissue --help")
    else:
        print("❌ Some dependencies are missing or incorrect.")
        print("Please install missing packages and run this check again.")
        
        # Show package information for debugging
        print("\n📦 Installed 'github' related packages:")
        for pkg in ["github", "PyGithub"]:
            info = get_package_info(pkg)
            if info:
                lines = info.split('\n')
                for line in lines[:3]:  # Show first 3 lines (Name, Version, Summary)
                    if line.strip():
                        print(f"   {line}")
                print()
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
