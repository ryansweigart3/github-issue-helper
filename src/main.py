#!/usr/bin/env python3
"""
GitHub Issues CLI - Create GitHub issues from CSV files

A command-line tool that reads issue data from CSV files and creates
corresponding issues in GitHub repositories.
"""

import sys
import os
import re
import click
from typing import Optional

from .csv_parser import CSVParser, IssueData
from .github_client import GitHubClient, BatchResult


# Global variables for controlling output verbosity
VERBOSE = False
QUIET = False


def log_info(message: str) -> None:
    """Log info message if not in quiet mode"""
    if not QUIET:
        click.echo(message)


def log_verbose(message: str) -> None:
    """Log verbose message if verbose mode is enabled"""
    if VERBOSE and not QUIET:
        click.echo(f"[VERBOSE] {message}")


def log_error(message: str) -> None:
    """Log error message (always shown unless quiet)"""
    if not QUIET:
        click.echo(f"Error: {message}", err=True)


def log_warning(message: str) -> None:
    """Log warning message if not in quiet mode"""
    if not QUIET:
        click.echo(f"Warning: {message}", err=True)


def validate_repo_format(repo: str) -> bool:
    """
    Validate that repo is in correct owner/repo format
    
    Args:
        repo: Repository string to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    # Basic pattern: owner/repo (allowing alphanumeric, hyphens, underscores, dots)
    pattern = r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'
    
    if not re.match(pattern, repo):
        return False
    
    # Additional validations
    parts = repo.split('/')
    if len(parts) != 2:
        return False
    
    owner, repo_name = parts
    
    # Check for empty parts
    if not owner.strip() or not repo_name.strip():
        return False
    
    # Check length constraints (GitHub limits)
    if len(owner) > 39 or len(repo_name) > 100:
        return False
    
    return True


def validate_file_exists(file_path: str) -> bool:
    """
    Validate that the CSV file exists and is readable
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        bool: True if file exists and is readable, False otherwise
    """
    if not os.path.exists(file_path):
        log_error(f"File not found: {file_path}")
        return False
    
    if not os.path.isfile(file_path):
        log_error(f"Path is not a file: {file_path}")
        return False
    
    if not os.access(file_path, os.R_OK):
        log_error(f"File is not readable: {file_path}")
        return False
    
    return True


def determine_exit_code(result: BatchResult) -> int:
    """
    Determine appropriate exit code based on batch result
    
    Args:
        result: BatchResult from GitHub client
        
    Returns:
        int: Exit code (0 for success, 1 for any failures)
    """
    if result.failed > 0:
        return 1
    return 0


@click.command()
@click.option(
    '--file', '-f',
    required=True,
    type=click.Path(exists=True, readable=True),
    help='Path to CSV file containing issue data'
)
@click.option(
    '--repo', '-r',
    required=True,
    help='GitHub repository in format "owner/repo-name"'
)
@click.option(
    '--token', '-t',
    required=True,
    help='GitHub personal access token'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output showing detailed progress'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress all output except errors and final summary'
)
@click.version_option(version='1.0.0', prog_name='github-issues-cli')
def main(file: str, repo: str, token: str, verbose: bool, quiet: bool) -> None:
    """
    Create GitHub issues from CSV file data.
    
    This tool reads issue information from a CSV file and creates corresponding
    issues in a GitHub repository. The CSV should contain columns for issue title,
    description, assignee, and labels.
    
    Example usage:
    
        github-issues-cli --file issues.csv --repo myorg/myproject --token ghp_xxx
    
    The CSV file should have flexible column headers like:
    - issue title, title, or summary (required)
    - description, desc, or details (required) 
    - assignee, assigned to, or owner (optional)
    - label, labels, or tags (optional)
    """
    global VERBOSE, QUIET
    
    # Set global flags for logging functions
    VERBOSE = verbose
    QUIET = quiet
    
    # Validate quiet and verbose aren't both set
    if quiet and verbose:
        click.echo("Error: --quiet and --verbose cannot be used together", err=True)
        sys.exit(1)
    
    log_verbose("Starting github-issues-cli")
    log_verbose(f"File: {file}")
    log_verbose(f"Repository: {repo}")
    log_verbose(f"Token: {'*' * (len(token) - 4)}{token[-4:] if len(token) > 4 else '***'}")
    
    # Validate inputs
    log_verbose("Validating inputs...")
    
    # Validate repository format
    if not validate_repo_format(repo):
        log_error(f"Invalid repository format: '{repo}'")
        log_error("Repository must be in format 'owner/repo-name'")
        sys.exit(1)
    
    log_verbose("Repository format is valid")
    
    # Validate file (Click already checks existence, but we add our own checks)
    if not validate_file_exists(file):
        sys.exit(1)
    
    log_verbose("CSV file validation passed")
    
    # Parse CSV file
    log_info("Parsing CSV file...")
    log_verbose(f"Reading CSV file: {file}")
    
    try:
        parser = CSVParser(file)
        issues = parser.parse()
        
        if not issues:
            log_error("No valid issues found in CSV file")
            sys.exit(1)
        
        log_info(f"Successfully parsed {len(issues)} issues from CSV")
        
        if VERBOSE:
            log_verbose("Column mappings:")
            for field, column in parser.get_column_mapping_info().items():
                log_verbose(f"  {field} -> {column}")
        
    except Exception as e:
        log_error(f"Failed to parse CSV file: {str(e)}")
        sys.exit(1)
    
    # Connect to GitHub
    log_info("Connecting to GitHub...")
    log_verbose(f"Initializing GitHub client for repository: {repo}")
    
    try:
        client = GitHubClient(token, repo)
        
        if not client.connect():
            log_error("Failed to connect to GitHub")
            sys.exit(1)
        
        log_verbose("GitHub connection successful")
        
    except Exception as e:
        log_error(f"Failed to initialize GitHub client: {str(e)}")
        sys.exit(1)
    
    # Create issues
    log_info(f"Creating {len(issues)} issues in {repo}...")
    
    try:
        # Redirect GitHub client output if in quiet mode
        if QUIET:
            # Temporarily capture print statements from GitHubClient
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            captured_output = io.StringIO()
            with redirect_stdout(captured_output), redirect_stderr(captured_output):
                result = client.create_issues_batch(issues)
        else:
            result = client.create_issues_batch(issues)
        
        log_verbose("Batch issue creation completed")
        
    except Exception as e:
        log_error(f"Failed to create issues: {str(e)}")
        sys.exit(1)
    
    # Show results
    if QUIET:
        # In quiet mode, only show the summary
        if result.successful > 0:
            click.echo(f"Successfully created {result.successful} issues")
        if result.failed > 0:
            click.echo(f"Failed to create {result.failed} issues", err=True)
        if result.skipped > 0:
            click.echo(f"Skipped {result.skipped} duplicate issues")
    else:
        # In normal/verbose mode, show full summary
        client.print_summary(result)
    
    # Provide additional verbose information
    if VERBOSE:
        log_verbose("Operation completed")
        log_verbose(f"Exit code will be: {determine_exit_code(result)}")
    
    # Exit with appropriate code
    sys.exit(determine_exit_code(result))


if __name__ == '__main__':
    main()





