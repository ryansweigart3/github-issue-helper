import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Import PyGithub with error handling for common installation issues
try:
    from github import Github, GithubException
    from github.Repository import Repository
    from github.Issue import Issue
except ImportError as e:
    print("Error: PyGithub package not found or incorrect 'github' package installed.")
    print("Please install the correct package:")
    print("  pip uninstall github")
    print("  pip install PyGithub")
    print(f"Original error: {e}")
    raise ImportError("PyGithub package required. Run: pip install PyGithub") from e

from src.csv_parser import IssueData


@dataclass
class IssueCreationResult:
    """Result of attempting to create a single issue"""
    success: bool
    issue_data: IssueData
    issue_url: Optional[str] = None
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None


@dataclass
class BatchResult:
    """Summary of batch issue creation"""
    total_issues: int
    successful: int
    failed: int
    skipped: int
    results: List[IssueCreationResult]


class GitHubClient:
    """GitHub client for creating issues from CSV data"""
    
    def __init__(self, token: str, repo_name: str):
        """
        Initialize GitHub client
        
        Args:
            token: GitHub personal access token
            repo_name: Repository name in format 'owner/repo'
        """
        self.token = token
        self.repo_name = repo_name
        self.github = None
        self.repo = None
        self._existing_issues_cache = None
        self._existing_labels_cache = None
        
    def connect(self) -> bool:
        """
        Connect to GitHub and validate repository access
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.github = Github(self.token)
            
            # Test authentication
            user = self.github.get_user()
            print(f"Connected to GitHub as: {user.login}")
            
            # Get repository
            self.repo = self.github.get_repo(self.repo_name)
            print(f"Repository: {self.repo.full_name}")
            
            return True
            
        except GithubException as e:
            if e.status == 401:
                print(f"Error: Invalid GitHub token or insufficient permissions")
            elif e.status == 404:
                print(f"Error: Repository '{self.repo_name}' not found or no access")
            else:
                print(f"Error connecting to GitHub: {e.data.get('message', str(e))}")
            return False
        except Exception as e:
            print(f"Unexpected error connecting to GitHub: {str(e)}")
            return False
    
    def create_issues_batch(self, issues: List[IssueData]) -> BatchResult:
        """
        Create multiple issues from IssueData objects
        
        Args:
            issues: List of IssueData objects to create
            
        Returns:
            BatchResult: Summary of the operation
        """
        if not self.repo:
            raise RuntimeError("Must call connect() successfully before creating issues")
        
        print(f"Starting batch creation of {len(issues)} issues...")
        
        # Cache existing issues and labels for efficiency
        self._cache_existing_issues()
        self._cache_existing_labels()
        
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        for i, issue_data in enumerate(issues, 1):
            print(f"Processing issue {i}/{len(issues)}: {issue_data.title}")
            
            result = self._create_single_issue(issue_data)
            results.append(result)
            
            if result.success:
                successful += 1
                print(f"  ✓ Created: {result.issue_url}")
            elif result.skipped:
                skipped += 1
                print(f"  ⊝ Skipped: {result.skip_reason}")
            else:
                failed += 1
                print(f"  ✗ Failed: {result.error_message}")
            
            # Be nice to GitHub's API - small delay between requests
            time.sleep(0.1)
        
        return BatchResult(
            total_issues=len(issues),
            successful=successful,
            failed=failed,
            skipped=skipped,
            results=results
        )
    
    def _create_single_issue(self, issue_data: IssueData) -> IssueCreationResult:
        """Create a single issue and return the result"""
        try:
            # Check for duplicate title
            if self._issue_title_exists(issue_data.title):
                return IssueCreationResult(
                    success=False,
                    issue_data=issue_data,
                    skipped=True,
                    skip_reason=f"Issue with title '{issue_data.title}' already exists"
                )
            
            # Validate and get assignee
            assignee = self._validate_assignee(issue_data.assignee)
            
            # Ensure labels exist
            labels = self._ensure_labels_exist(issue_data.labels)
            
            # Create the issue
            issue = self.repo.create_issue(
                title=issue_data.title,
                body=issue_data.description,
                assignee=assignee,
                labels=labels
            )
            
            return IssueCreationResult(
                success=True,
                issue_data=issue_data,
                issue_url=issue.html_url
            )
            
        except GithubException as e:
            error_msg = f"GitHub API error: {e.data.get('message', str(e))}"
            return IssueCreationResult(
                success=False,
                issue_data=issue_data,
                error_message=error_msg
            )
        except Exception as e:
            return IssueCreationResult(
                success=False,
                issue_data=issue_data,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _cache_existing_issues(self) -> None:
        """Cache existing issue titles for duplicate checking"""
        print("Caching existing issues...")
        try:
            # Get open issues (most common case for duplicates)
            issues = self.repo.get_issues(state='open')
            self._existing_issues_cache = {issue.title.lower() for issue in issues}
            print(f"Found {len(self._existing_issues_cache)} existing open issues")
        except Exception as e:
            print(f"Warning: Could not cache existing issues: {str(e)}")
            self._existing_issues_cache = set()
    
    def _cache_existing_labels(self) -> None:
        """Cache existing labels"""
        print("Caching existing labels...")
        try:
            labels = self.repo.get_labels()
            self._existing_labels_cache = {label.name.lower(): label.name for label in labels}
            print(f"Found {len(self._existing_labels_cache)} existing labels")
        except Exception as e:
            print(f"Warning: Could not cache existing labels: {str(e)}")
            self._existing_labels_cache = {}
    
    def _issue_title_exists(self, title: str) -> bool:
        """Check if an issue with this title already exists"""
        if self._existing_issues_cache is None:
            return False
        return title.lower() in self._existing_issues_cache
    
    def _validate_assignee(self, assignee: Optional[str]) -> Optional[str]:
        """
        Validate assignee exists in repository
        
        Args:
            assignee: Username to assign
            
        Returns:
            Valid assignee username or None
        """
        if not assignee:
            return None
        
        try:
            # Check if user has access to repository
            self.repo.get_collaborator_permission(assignee)
            return assignee
        except GithubException as e:
            if e.status == 404:
                print(f"  Warning: Assignee '{assignee}' not found or no repo access. Creating issue without assignee.")
            else:
                print(f"  Warning: Could not validate assignee '{assignee}': {e.data.get('message', str(e))}. Creating issue without assignee.")
            return None
        except Exception as e:
            print(f"  Warning: Error validating assignee '{assignee}': {str(e)}. Creating issue without assignee.")
            return None
    
    def _ensure_labels_exist(self, labels: List[str]) -> List[str]:
        """
        Ensure all labels exist in repository, create if necessary
        
        Args:
            labels: List of label names
            
        Returns:
            List of valid label names
        """
        if not labels:
            return []
        
        valid_labels = []
        
        for label in labels:
            # Check if label exists (case-insensitive)
            existing_label = self._existing_labels_cache.get(label.lower())
            
            if existing_label:
                # Use the existing label name (preserves original case)
                valid_labels.append(existing_label)
            else:
                # Create new label
                try:
                    new_label = self.repo.create_label(
                        name=label,
                        color="0075ca",  # Default blue color
                        description=f"Label created automatically by tissue"
                    )
                    valid_labels.append(new_label.name)
                    # Update cache
                    self._existing_labels_cache[label.lower()] = new_label.name
                    print(f"  Created new label: '{label}'")
                    
                except GithubException as e:
                    print(f"  Warning: Could not create label '{label}': {e.data.get('message', str(e))}")
                    # Skip this label but continue with others
                    continue
                except Exception as e:
                    print(f"  Warning: Error creating label '{label}': {str(e)}")
                    continue
        
        return valid_labels
    
    def print_summary(self, result: BatchResult) -> None:
        """Print a formatted summary of the batch operation"""
        print("\n" + "="*60)
        print("BATCH ISSUE CREATION SUMMARY")
        print("="*60)
        print(f"Total issues processed: {result.total_issues}")
        print(f"Successfully created:   {result.successful}")
        print(f"Skipped (duplicates):   {result.skipped}")
        print(f"Failed:                 {result.failed}")
        print("="*60)
        
        if result.failed > 0:
            print("\nFAILED ISSUES:")
            for r in result.results:
                if not r.success and not r.skipped:
                    print(f"  • {r.issue_data.title}: {r.error_message}")
        
        if result.skipped > 0:
            print("\nSKIPPED ISSUES:")
            for r in result.results:
                if r.skipped:
                    print(f"  • {r.issue_data.title}: {r.skip_reason}")
        
        if result.successful > 0:
            print(f"\n✓ Successfully created {result.successful} issues!")
        
        print()


# Example usage
if __name__ == "__main__":
    # This would be used for testing
    # client = GitHubClient("your_token", "owner/repo")
    # if client.connect():
    #     issues = [...]  # from CSV parser
    #     result = client.create_issues_batch(issues)
    #     client.print_summary(result)
    pass

