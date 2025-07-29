import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from github import GithubException

from src.github_client import GitHubClient, IssueCreationResult, BatchResult
from src.csv_parser import IssueData


class TestGitHubClient(unittest.TestCase):
    """Test suite for GitHubClient class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.token = "ghp_test_token_12345"
        self.repo_name = "testuser/testrepo"
        self.client = GitHubClient(self.token, self.repo_name)
        
        # Sample issue data for testing
        self.sample_issue_data = IssueData(
            title="Test Issue",
            description="Test Description",
            assignee="testuser",
            labels=["bug", "high-priority"]
        )
    
    @patch('src.github_client.Github')
    def test_connect_success(self, mock_github_class):
        """Test successful connection to GitHub"""
        # Mock GitHub objects
        mock_github = Mock()
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_repo = Mock()
        mock_repo.full_name = "testuser/testrepo"
        
        mock_github.get_user.return_value = mock_user
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github
        
        # Test connection
        result = self.client.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.client.github, mock_github)
        self.assertEqual(self.client.repo, mock_repo)
        mock_github_class.assert_called_once_with(self.token)
        mock_github.get_user.assert_called_once()
        mock_github.get_repo.assert_called_once_with(self.repo_name)
    
    @patch('src.github_client.Github')
    def test_connect_invalid_token(self, mock_github_class):
        """Test connection with invalid token"""
        mock_github = Mock()
        mock_github.get_user.side_effect = GithubException(401, {"message": "Bad credentials"}, {})
        mock_github_class.return_value = mock_github
        
        result = self.client.connect()
        
        self.assertFalse(result)
        self.assertIsNone(self.client.repo)
    
    @patch('src.github_client.Github')
    def test_connect_repo_not_found(self, mock_github_class):
        """Test connection with non-existent repository"""
        mock_github = Mock()
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_github.get_user.return_value = mock_user
        mock_github.get_repo.side_effect = GithubException(404, {"message": "Not Found"}, {})
        mock_github_class.return_value = mock_github
        
        result = self.client.connect()
        
        self.assertFalse(result)
        self.assertIsNone(self.client.repo)
    
    def test_issue_title_exists(self):
        """Test duplicate title detection"""
        # Set up mock cache
        self.client._existing_issues_cache = {"existing issue", "another issue"}
        
        # Test existing title
        self.assertTrue(self.client._issue_title_exists("Existing Issue"))
        self.assertTrue(self.client._issue_title_exists("EXISTING ISSUE"))
        
        # Test non-existing title
        self.assertFalse(self.client._issue_title_exists("New Issue"))
        
        # Test with no cache
        self.client._existing_issues_cache = None
        self.assertFalse(self.client._issue_title_exists("Any Issue"))
    
    def test_validate_assignee_valid(self):
        """Test assignee validation with valid user"""
        mock_repo = Mock()
        mock_repo.get_collaborator_permission.return_value = Mock()
        self.client.repo = mock_repo
        
        result = self.client._validate_assignee("validuser")
        
        self.assertEqual(result, "validuser")
        mock_repo.get_collaborator_permission.assert_called_once_with("validuser")
    
    def test_validate_assignee_invalid(self):
        """Test assignee validation with invalid user"""
        mock_repo = Mock()
        mock_repo.get_collaborator_permission.side_effect = GithubException(404, {"message": "Not Found"}, {})
        self.client.repo = mock_repo
        
        with patch('builtins.print'):  # Suppress warning output
            result = self.client._validate_assignee("invaliduser")
        
        self.assertIsNone(result)
    
    def test_validate_assignee_none(self):
        """Test assignee validation with None"""
        result = self.client._validate_assignee(None)
        self.assertIsNone(result)
    
    def test_ensure_labels_exist_all_existing(self):
        """Test label creation when all labels already exist"""
        self.client._existing_labels_cache = {
            "bug": "bug",
            "high-priority": "high-priority"
        }
        
        result = self.client._ensure_labels_exist(["bug", "high-priority"])
        
        self.assertEqual(result, ["bug", "high-priority"])
    
    def test_ensure_labels_exist_create_new(self):
        """Test label creation when labels don't exist"""
        mock_repo = Mock()
        mock_new_label = Mock()
        mock_new_label.name = "new-label"
        mock_repo.create_label.return_value = mock_new_label
        self.client.repo = mock_repo
        self.client._existing_labels_cache = {}
        
        with patch('builtins.print'):  # Suppress output
            result = self.client._ensure_labels_exist(["new-label"])
        
        self.assertEqual(result, ["new-label"])
        mock_repo.create_label.assert_called_once_with(
            name="new-label",
            color="0075ca",
            description="Label created automatically by tissue"
        )
    
    def test_ensure_labels_exist_creation_fails(self):
        """Test label creation when GitHub API fails"""
        mock_repo = Mock()
        mock_repo.create_label.side_effect = GithubException(422, {"message": "Validation Failed"}, {})
        self.client.repo = mock_repo
        self.client._existing_labels_cache = {}
        
        with patch('builtins.print'):  # Suppress warning output
            result = self.client._ensure_labels_exist(["failing-label"])
        
        self.assertEqual(result, [])  # Should return empty list when creation fails
    
    def test_ensure_labels_exist_empty_list(self):
        """Test label creation with empty list"""
        result = self.client._ensure_labels_exist([])
        self.assertEqual(result, [])
    
    @patch('src.github_client.time.sleep')
    def test_create_single_issue_success(self, mock_sleep):
        """Test successful creation of a single issue"""
        # Setup mocks
        mock_repo = Mock()
        mock_issue = Mock()
        mock_issue.html_url = "https://github.com/testuser/testrepo/issues/123"
        mock_repo.create_issue.return_value = mock_issue
        
        self.client.repo = mock_repo
        self.client._existing_issues_cache = set()
        self.client._existing_labels_cache = {"bug": "bug", "high-priority": "high-priority"}
        
        # Mock assignee validation
        with patch.object(self.client, '_validate_assignee', return_value="testuser"):
            result = self.client._create_single_issue(self.sample_issue_data)
        
        self.assertTrue(result.success)
        self.assertFalse(result.skipped)
        self.assertEqual(result.issue_url, "https://github.com/testuser/testrepo/issues/123")
        self.assertEqual(result.issue_data, self.sample_issue_data)
        
        mock_repo.create_issue.assert_called_once_with(
            title="Test Issue",
            body="Test Description",
            assignee="testuser",
            labels=["bug", "high-priority"]
        )
    
    def test_create_single_issue_duplicate(self):
        """Test skipping duplicate issue"""
        self.client._existing_issues_cache = {"test issue"}
        
        result = self.client._create_single_issue(self.sample_issue_data)
        
        self.assertFalse(result.success)
        self.assertTrue(result.skipped)
        self.assertIn("already exists", result.skip_reason)
    
    def test_create_single_issue_api_error(self):
        """Test handling of GitHub API errors"""
        mock_repo = Mock()
        mock_repo.create_issue.side_effect = GithubException(422, {"message": "Validation Failed"}, {})
        
        self.client.repo = mock_repo
        self.client._existing_issues_cache = set()
        self.client._existing_labels_cache = {}
        
        with patch.object(self.client, '_validate_assignee', return_value=None):
            with patch.object(self.client, '_ensure_labels_exist', return_value=[]):
                result = self.client._create_single_issue(self.sample_issue_data)
        
        self.assertFalse(result.success)
        self.assertFalse(result.skipped)
        self.assertIn("GitHub API error", result.error_message)
    
    @patch('src.github_client.time.sleep')
    def test_create_issues_batch_success(self, mock_sleep):
        """Test successful batch creation of issues"""
        # Setup
        issues = [
            IssueData("Issue 1", "Description 1", "user1", ["bug"]),
            IssueData("Issue 2", "Description 2", "user2", ["enhancement"]),
        ]
        
        mock_repo = Mock()
        mock_issue1 = Mock()
        mock_issue1.html_url = "https://github.com/testuser/testrepo/issues/1"
        mock_issue2 = Mock()
        mock_issue2.html_url = "https://github.com/testuser/testrepo/issues/2"
        mock_repo.create_issue.side_effect = [mock_issue1, mock_issue2]
        
        self.client.repo = mock_repo
        
        # Mock cache methods
        with patch.object(self.client, '_cache_existing_issues'):
            with patch.object(self.client, '_cache_existing_labels'):
                with patch.object(self.client, '_issue_title_exists', return_value=False):
                    with patch.object(self.client, '_validate_assignee', side_effect=["user1", "user2"]):
                        with patch.object(self.client, '_ensure_labels_exist', side_effect=[["bug"], ["enhancement"]]):
                            with patch('builtins.print'):  # Suppress output
                                result = self.client.create_issues_batch(issues)
        
        self.assertEqual(result.total_issues, 2)
        self.assertEqual(result.successful, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual(result.skipped, 0)
    
    @patch('src.github_client.time.sleep')
    def test_create_issues_batch_mixed_results(self, mock_sleep):
        """Test batch creation with mixed success/failure/skip results"""
        issues = [
            IssueData("Success Issue", "Description", "user1", ["bug"]),
            IssueData("Duplicate Issue", "Description", "user2", ["enhancement"]),
            IssueData("Failing Issue", "Description", "user3", ["documentation"]),
        ]
        
        mock_repo = Mock()
        mock_issue = Mock()
        mock_issue.html_url = "https://github.com/testuser/testrepo/issues/1"
        mock_repo.create_issue.side_effect = [
            mock_issue,  # Success
            GithubException(422, {"message": "Validation Failed"}, {}),  # Failure
        ]
        
        self.client.repo = mock_repo
        
        with patch.object(self.client, '_cache_existing_issues'):
            with patch.object(self.client, '_cache_existing_labels'):
                with patch.object(self.client, '_issue_title_exists', side_effect=[False, True, False]):
                    with patch.object(self.client, '_validate_assignee', return_value="user"):
                        with patch.object(self.client, '_ensure_labels_exist', return_value=["label"]):
                            with patch('builtins.print'):  # Suppress output
                                result = self.client.create_issues_batch(issues)
        
        self.assertEqual(result.total_issues, 3)
        self.assertEqual(result.successful, 1)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.skipped, 1)
    
    def test_create_issues_batch_no_connection(self):
        """Test batch creation without established connection"""
        issues = [self.sample_issue_data]
        
        with self.assertRaises(RuntimeError) as context:
            self.client.create_issues_batch(issues)
        
        self.assertIn("Must call connect()", str(context.exception))
    
    def test_cache_existing_issues_success(self):
        """Test caching of existing issues"""
        mock_repo = Mock()
        mock_issue1 = Mock()
        mock_issue1.title = "Existing Issue 1"
        mock_issue2 = Mock()
        mock_issue2.title = "Existing Issue 2"
        mock_repo.get_issues.return_value = [mock_issue1, mock_issue2]
        
        self.client.repo = mock_repo
        
        with patch('builtins.print'):  # Suppress output
            self.client._cache_existing_issues()
        
        expected_cache = {"existing issue 1", "existing issue 2"}
        self.assertEqual(self.client._existing_issues_cache, expected_cache)
        mock_repo.get_issues.assert_called_once_with(state='open')
    
    def test_cache_existing_issues_failure(self):
        """Test handling of caching failure"""
        mock_repo = Mock()
        mock_repo.get_issues.side_effect = GithubException(403, {"message": "Forbidden"}, {})
        
        self.client.repo = mock_repo
        
        with patch('builtins.print'):  # Suppress warning output
            self.client._cache_existing_issues()
        
        self.assertEqual(self.client._existing_issues_cache, set())
    
    def test_cache_existing_labels_success(self):
        """Test caching of existing labels"""
        mock_repo = Mock()
        mock_label1 = Mock()
        mock_label1.name = "bug"
        mock_label2 = Mock()
        mock_label2.name = "Enhancement"
        mock_repo.get_labels.return_value = [mock_label1, mock_label2]
        
        self.client.repo = mock_repo
        
        with patch('builtins.print'):  # Suppress output
            self.client._cache_existing_labels()
        
        expected_cache = {"bug": "bug", "enhancement": "Enhancement"}
        self.assertEqual(self.client._existing_labels_cache, expected_cache)
    
    def test_print_summary(self):
        """Test summary printing functionality"""
        result = BatchResult(
            total_issues=5,
            successful=3,
            failed=1,
            skipped=1,
            results=[
                IssueCreationResult(True, self.sample_issue_data, "https://github.com/test/repo/issues/1"),
                IssueCreationResult(False, self.sample_issue_data, error_message="API Error"),
                IssueCreationResult(False, self.sample_issue_data, skipped=True, skip_reason="Duplicate"),
            ]
        )
        
        with patch('builtins.print') as mock_print:
            self.client.print_summary(result)
        
        # Verify that print was called (summary was displayed)
        self.assertTrue(mock_print.called)
        
        # Check that key information appears in the printed output
        printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
        self.assertIn("Total issues processed: 5", printed_text)
        self.assertIn("Successfully created:   3", printed_text)
        self.assertIn("Failed:                 1", printed_text)
        self.assertIn("Skipped (duplicates):   1", printed_text)


class TestIssueCreationResult(unittest.TestCase):
    """Test suite for IssueCreationResult dataclass"""
    
    def test_successful_result(self):
        """Test creation of successful result"""
        issue_data = IssueData("Test", "Description")
        result = IssueCreationResult(
            success=True,
            issue_data=issue_data,
            issue_url="https://github.com/test/repo/issues/1"
        )
        
        self.assertTrue(result.success)
        self.assertFalse(result.skipped)
        self.assertEqual(result.issue_url, "https://github.com/test/repo/issues/1")
        self.assertIsNone(result.error_message)
    
    def test_failed_result(self):
        """Test creation of failed result"""
        issue_data = IssueData("Test", "Description")
        result = IssueCreationResult(
            success=False,
            issue_data=issue_data,
            error_message="API Error"
        )
        
        self.assertFalse(result.success)
        self.assertFalse(result.skipped)
        self.assertEqual(result.error_message, "API Error")
        self.assertIsNone(result.issue_url)
    
    def test_skipped_result(self):
        """Test creation of skipped result"""
        issue_data = IssueData("Test", "Description")
        result = IssueCreationResult(
            success=False,
            issue_data=issue_data,
            skipped=True,
            skip_reason="Duplicate title"
        )
        
        self.assertFalse(result.success)
        self.assertTrue(result.skipped)
        self.assertEqual(result.skip_reason, "Duplicate title")


class TestBatchResult(unittest.TestCase):
    """Test suite for BatchResult dataclass"""
    
    def test_batch_result_creation(self):
        """Test creation of batch result"""
        results = [
            IssueCreationResult(True, IssueData("Test1", "Desc1")),
            IssueCreationResult(False, IssueData("Test2", "Desc2"), error_message="Error"),
        ]
        
        batch_result = BatchResult(
            total_issues=2,
            successful=1,
            failed=1,
            skipped=0,
            results=results
        )
        
        self.assertEqual(batch_result.total_issues, 2)
        self.assertEqual(batch_result.successful, 1)
        self.assertEqual(batch_result.failed, 1)
        self.assertEqual(batch_result.skipped, 0)
        self.assertEqual(len(batch_result.results), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
