#!/usr/bin/env python3
"""
Setup script for github-issues-cli
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "A CLI tool for creating GitHub issues from CSV files"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle version specifiers and comments
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    requirements.append(line)
    
    # Ensure PyGithub is explicitly listed to avoid naming conflicts
    core_requirements = [
        "PyGithub>=1.58.0",
        "click>=8.0.0", 
        "pandas>=1.5.0",
        "requests>=2.28.0"
    ]
    
    # Add core requirements if not already present
    for req in core_requirements:
        package_name = req.split('>=')[0].split('==')[0]
        if not any(package_name in existing_req for existing_req in requirements):
            requirements.append(req)
    
    return requirements

setup(
    name="tissue",
    version="1.1.0",
    author="Ryan Sweigart", 
    author_email="coffeedatadev@gmail.com",
    description="A CLI tool for creating GitHub issues from CSV files",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ryansweigart3/tissue",  # Replace with your repo URL
    project_urls={
        "Bug Reports": "https://github.com/ryansweigart3/tissue/issues",
        "Source": "https://github.com/ryansweigart3/tissue",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tissue=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="github issues csv cli automation tissue",
)


