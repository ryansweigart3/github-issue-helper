from setuptools import setup, find_packages

setup(
    name="github-issues-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "PyGithub", 
        "pandas",
        "python-dotenv",
        "colorama"
    ]
)
