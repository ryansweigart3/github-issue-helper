"""
Tissue - Create GitHub issues from CSV files

A command-line tool that reads issue data from CSV files and creates
corresponding issues in GitHub repositories.
"""

__version__ = "1.0.0"
__author__ = "Ryan Sweigart"

# Make key classes available at package level
try:
    from .src.csv_parser import CSVParser, IssueData
    from .src.github_client import GitHubClient, IssueCreationResult, BatchResult
except ImportError:
    # During installation, src modules might not be available yet
    pass
