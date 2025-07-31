import time
import json
import requests
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

# Import PyGithub with error handling
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


@dataclass
class ProjectField:
    """Represents a custom field in a GitHub project"""
    id: str
    name: str
    data_type: str  # TEXT, SINGLE_SELECT, NUMBER, DATE, ITERATION
    options: List[str] = None  # For SINGLE_SELECT fields
    
    def __post_init__(self):
        if self.options is None:
            self.options = []


@dataclass
class ProjectColumn:
    """Represents a column/status in a GitHub project"""
    id: str
    name: str
    is_default: bool = False


@dataclass
class ProjectInfo:
    """Information about a GitHub project"""
    id: str
    number: int
    title: str
    url: str
    columns: List[ProjectColumn]
    custom_fields: List[ProjectField]


class GitHubProjectsClient:
    """Client for GitHub Projects v2 integration using GraphQL API"""
    
    def __init__(self, github_client: Github, repo: Repository, token: str):
        """
        Initialize Projects client
        
        Args:
            github_client: Authenticated GitHub client
            repo: Repository object
            token: GitHub personal access token
        """
        self.github = github_client
        self.repo = repo
        self.token = token
        self.graphql_url = "https://api.github.com/graphql"
        self._projects_cache = None
        
    def _execute_graphql_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against GitHub's API"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = requests.post(self.graphql_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code} {response.text}")
        
        result = response.json()
        
        if "errors" in result:
            errors = "; ".join([error["message"] for error in result["errors"]])
            raise Exception(f"GraphQL errors: {errors}")
        
        return result["data"]
        
    def get_projects(self) -> List[ProjectInfo]:
        """Get all projects associated with the repository and organization"""
        if self._projects_cache is not None:
            return self._projects_cache
            
        try:
            owner, repo_name = self.repo.full_name.split('/')
            projects = []
            
            # Query for repository projects
            repo_projects = self._get_repository_projects(owner, repo_name)
            projects.extend(repo_projects)
            
            # Query for organization projects (if owner is an organization)
            org_projects = self._get_organization_projects(owner)
            projects.extend(org_projects)
            
            # Query for user projects (if owner is a user)
            user_projects = self._get_user_projects(owner)
            projects.extend(user_projects)
            
            self._projects_cache = projects
            return projects
            
        except Exception as e:
            print(f"Warning: Could not fetch projects: {str(e)}")
            return []
    
    def _get_repository_projects(self, owner: str, repo: str) -> List[ProjectInfo]:
        """Get projects at the repository level"""
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            projectsV2(first: 20) {
              nodes {
                id
                number
                title
                url
                fields(first: 50) {
                  nodes {
                    ... on ProjectV2Field {
                      id
                      name
                      dataType
                    }
                    ... on ProjectV2SingleSelectField {
                      id
                      name
                      dataType
                      options {
                        id
                        name
                      }
                    }
                    ... on ProjectV2IterationField {
                      id
                      name
                      dataType
                    }
                  }
                }
                views(first: 5) {
                  nodes {
                    id
                    name
                    layout
                    ... on ProjectV2View {
                      groupBy {
                        ... on ProjectV2Field {
                          id
                          name
                        }
                        ... on ProjectV2SingleSelectField {
                          id
                          name
                          options {
                            id
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            data = self._execute_graphql_query(query, {"owner": owner, "repo": repo})
            projects = []
            
            if data.get("repository") and data["repository"].get("projectsV2"):
                for project_data in data["repository"]["projectsV2"]["nodes"]:
                    project = self._parse_project_data(project_data)
                    if project:
                        projects.append(project)
            
            return projects
        except Exception as e:
            print(f"Warning: Could not fetch repository projects: {str(e)}")
            return []
    
    def _get_organization_projects(self, owner: str) -> List[ProjectInfo]:
        """Get projects at the organization level"""
        query = """
        query($owner: String!) {
          organization(login: $owner) {
            projectsV2(first: 20) {
              nodes {
                id
                number
                title
                url
                fields(first: 50) {
                  nodes {
                    ... on ProjectV2Field {
                      id
                      name
                      dataType
                    }
                    ... on ProjectV2SingleSelectField {
                      id
                      name
                      dataType
                      options {
                        id
                        name
                      }
                    }
                  }
                }
                views(first: 5) {
                  nodes {
                    id
                    name
                    layout
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            data = self._execute_graphql_query(query, {"owner": owner})
            projects = []
            
            if data.get("organization") and data["organization"].get("projectsV2"):
                for project_data in data["organization"]["projectsV2"]["nodes"]:
                    project = self._parse_project_data(project_data)
                    if project:
                        projects.append(project)
            
            return projects
        except Exception as e:
            print(f"Warning: Could not fetch organization projects: {str(e)}")
            return []
    
    def _get_user_projects(self, owner: str) -> List[ProjectInfo]:
        """Get projects at the user level"""
        query = """
        query($owner: String!) {
          user(login: $owner) {
            projectsV2(first: 20) {
              nodes {
                id
                number
                title
                url
                fields(first: 50) {
                  nodes {
                    ... on ProjectV2Field {
                      id
                      name
                      dataType
                    }
                    ... on ProjectV2SingleSelectField {
                      id
                      name
                      dataType
                      options {
                        id
                        name
                      }
                    }
                  }
                }
                views(first: 5) {
                  nodes {
                    id
                    name
                    layout
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            data = self._execute_graphql_query(query, {"owner": owner})
            projects = []
            
            if data.get("user") and data["user"].get("projectsV2"):
                for project_data in data["user"]["projectsV2"]["nodes"]:
                    project = self._parse_project_data(project_data)
                    if project:
                        projects.append(project)
            
            return projects
        except Exception as e:
            print(f"Warning: Could not fetch user projects: {str(e)}")
            return []
    
    def _parse_project_data(self, project_data: Dict[str, Any]) -> Optional[ProjectInfo]:
        """Parse project data from GraphQL response into ProjectInfo object"""
        try:
            # Parse custom fields
            custom_fields = []
            if project_data.get("fields") and project_data["fields"].get("nodes"):
                for field_data in project_data["fields"]["nodes"]:
                    if field_data["name"].lower() in ["title", "assignees", "labels", "repository"]:
                        continue  # Skip built-in fields
                    
                    options = []
                    if field_data.get("options"):
                        options = [opt["name"] for opt in field_data["options"]]
                    
                    field = ProjectField(
                        id=field_data["id"],
                        name=field_data["name"],
                        data_type=field_data["dataType"],
                        options=options
                    )
                    custom_fields.append(field)
            
            # Parse columns/views (Projects v2 uses views instead of columns)
            columns = []
            if project_data.get("views") and project_data["views"].get("nodes"):
                for view_data in project_data["views"]["nodes"]:
                    column = ProjectColumn(
                        id=view_data["id"],
                        name=view_data["name"],
                        is_default=(view_data["name"].lower() in ["board view", "table view"])
                    )
                    columns.append(column)
            
            # Add default status columns that are common in Projects v2
            status_field = next((f for f in custom_fields if f.name.lower() == "status"), None)
            if status_field and status_field.options:
                for i, option in enumerate(status_field.options):
                    column = ProjectColumn(
                        id=f"status-{option.lower().replace(' ', '-')}",
                        name=option,
                        is_default=(i == 0 or option.lower() in ["todo", "backlog", "new"])
                    )
                    columns.append(column)
            
            return ProjectInfo(
                id=project_data["id"],
                number=project_data["number"],
                title=project_data["title"],
                url=project_data["url"],
                columns=columns,
                custom_fields=custom_fields
            )
            
        except Exception as e:
            print(f"Warning: Could not parse project data: {str(e)}")
            return None
    
    def find_project_by_name(self, project_name: str) -> Optional[ProjectInfo]:
        """Find a project by its name"""
        projects = self.get_projects()
        
        for project in projects:
            if project.title.lower() == project_name.lower():
                return project
        
        return None
    
    def add_issue_to_project(self, project: ProjectInfo, issue: Issue, 
                           status: Optional[str] = None, 
                           custom_fields: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an issue to a project with optional status and custom fields
        
        Args:
            project: Project to add issue to
            issue: GitHub issue object
            status: Column/status to place issue in
            custom_fields: Custom field values to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"  → Adding issue to project '{project.title}'")
            
            # Step 1: Add issue to project
            item_id = self._add_issue_to_project_board(project.id, issue.node_id)
            
            if not item_id:
                return False
            
            # Step 2: Set status if provided
            if status:
                self._set_project_item_status(project, item_id, status)
            
            # Step 3: Set custom fields if provided
            if custom_fields:
                self._set_project_item_custom_fields(project, item_id, custom_fields)
            
            return True
            
        except Exception as e:
            print(f"  Warning: Could not add issue to project: {str(e)}")
            return False
    
    def _add_issue_to_project_board(self, project_id: str, issue_node_id: str) -> Optional[str]:
        """Add an issue to a project board and return the project item ID"""
        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item {
              id
            }
          }
        }
        """
        
        try:
            data = self._execute_graphql_query(mutation, {
                "projectId": project_id,
                "contentId": issue_node_id
            })
            
            if data.get("addProjectV2ItemById") and data["addProjectV2ItemById"].get("item"):
                return data["addProjectV2ItemById"]["item"]["id"]
            
            return None
            
        except Exception as e:
            print(f"    Warning: Could not add issue to project board: {str(e)}")
            return None
    
    def _set_project_item_status(self, project: ProjectInfo, item_id: str, status: str) -> bool:
        """Set the status of a project item"""
        # Find the Status field
        status_field = next((f for f in project.custom_fields if f.name.lower() == "status"), None)
        
        if not status_field:
            print(f"    Warning: No 'Status' field found in project")
            return False
        
        # Find the status option
        status_option = next((opt for opt in status_field.options if opt.lower() == status.lower()), None)
        
        if not status_option:
            print(f"    Warning: Status '{status}' not found in project")
            return False
        
        # Get the option ID
        status_option_id = self._get_field_option_id(status_field.id, status_option)
        
        if not status_option_id:
            return False
        
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: $value
          }) {
            projectV2Item {
              id
            }
          }
        }
        """
        
        try:
            self._execute_graphql_query(mutation, {
                "projectId": project.id,
                "itemId": item_id,
                "fieldId": status_field.id,
                "value": {"singleSelectOptionId": status_option_id}
            })
            
            print(f"    Status: {status}")
            return True
            
        except Exception as e:
            print(f"    Warning: Could not set status: {str(e)}")
            return False
    
    def _set_project_item_custom_fields(self, project: ProjectInfo, item_id: str, custom_fields: Dict[str, Any]) -> None:
        """Set custom field values for a project item"""
        for field_name, field_value in custom_fields.items():
            try:
                # Find the field
                field = next((f for f in project.custom_fields if f.name.lower() == field_name.lower()), None)
                
                if not field:
                    print(f"    Warning: Field '{field_name}' not found in project")
                    continue
                
                # Set the field value based on type
                success = self._set_single_custom_field(project, item_id, field, field_value)
                
                if success:
                    print(f"    {field_name}: {field_value}")
                    
            except Exception as e:
                print(f"    Warning: Could not set field '{field_name}': {str(e)}")
    
    def _set_single_custom_field(self, project: ProjectInfo, item_id: str, field: ProjectField, value: Any) -> bool:
        """Set a single custom field value"""
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: $value
          }) {
            projectV2Item {
              id
            }
          }
        }
        """
        
        # Prepare value based on field type
        field_value = None
        
        if field.data_type == "SINGLE_SELECT":
            option_id = self._get_field_option_id(field.id, str(value))
            if option_id:
                field_value = {"singleSelectOptionId": option_id}
        elif field.data_type == "TEXT":
            field_value = {"text": str(value)}
        elif field.data_type == "NUMBER":
            try:
                field_value = {"number": float(value)}
            except ValueError:
                print(f"    Warning: Invalid number value for field '{field.name}': {value}")
                return False
        elif field.data_type == "DATE":
            field_value = {"date": str(value)}  # Expects ISO date format
        else:
            print(f"    Warning: Unsupported field type '{field.data_type}' for field '{field.name}'")
            return False
        
        if not field_value:
            return False
        
        try:
            self._execute_graphql_query(mutation, {
                "projectId": project.id,
                "itemId": item_id,
                "fieldId": field.id,
                "value": field_value
            })
            return True
            
        except Exception as e:
            print(f"    Warning: Could not set field '{field.name}': {str(e)}")
            return False
    
    def _get_field_option_id(self, field_id: str, option_name: str) -> Optional[str]:
        """Get the ID of a field option by name"""
        query = """
        query($fieldId: ID!) {
          node(id: $fieldId) {
            ... on ProjectV2SingleSelectField {
              options {
                id
                name
              }
            }
          }
        }
        """
        
        try:
            data = self._execute_graphql_query(query, {"fieldId": field_id})
            
            if data.get("node") and data["node"].get("options"):
                for option in data["node"]["options"]:
                    if option["name"].lower() == option_name.lower():
                        return option["id"]
            
            return None
            
        except Exception as e:
            print(f"    Warning: Could not get field option ID: {str(e)}")
            return None
    
    def validate_project_fields(self, project: ProjectInfo, 
                               status: Optional[str] = None,
                               custom_fields: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """
        Validate that provided status and custom fields exist in the project
        
        Args:
            project: Project to validate against
            status: Status/column name to validate
            custom_fields: Custom fields to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate status/column
        if status:
            valid_columns = [col.name.lower() for col in project.columns]
            if status.lower() not in valid_columns:
                available = ", ".join([col.name for col in project.columns])
                errors.append(f"Invalid status '{status}'. Available: {available}")
        
        # Validate custom fields
        if custom_fields:
            valid_fields = {field.name.lower(): field for field in project.custom_fields}
            
            for field_name, value in custom_fields.items():
                field_name_lower = field_name.lower()
                
                if field_name_lower not in valid_fields:
                    available = ", ".join([field.name for field in project.custom_fields])
                    errors.append(f"Invalid field '{field_name}'. Available: {available}")
                    continue
                
                field = valid_fields[field_name_lower]
                
                # Validate field value based on type
                if field.data_type == "SINGLE_SELECT" and field.options:
                    valid_options = [opt.lower() for opt in field.options]
                    if str(value).lower() not in valid_options:
                        available_opts = ", ".join(field.options)
                        errors.append(f"Invalid value '{value}' for field '{field_name}'. Available: {available_opts}")
        
        return len(errors) == 0, errors
    
    def get_default_status(self, project: ProjectInfo) -> Optional[str]:
        """Get the default status/column for new issues"""
        # Look for common default column names
        default_names = ["backlog", "todo", "to do", "new", "inbox", "triage"]
        
        for column in project.columns:
            if column.is_default:
                return column.name
            
            if column.name.lower() in default_names:
                return column.name
        
        # If no default found, return first column
        if project.columns:
            return project.columns[0].name
        
        return None
    
    def parse_project_fields_from_csv_row(self, project: ProjectInfo, 
                                        row_data: Dict[str, str]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Parse project-related fields from a CSV row
        
        Args:
            project: Project info for validation
            row_data: Dictionary of CSV row data
            
        Returns:
            Tuple of (status, custom_fields_dict)
        """
        status = None
        custom_fields = {}
        
        # Look for status/column field
        status_keys = ["status", "column", "project_status", "state"]
        for key in status_keys:
            if key in row_data and row_data[key]:
                status = row_data[key].strip()
                break
        
        # Look for custom fields that match project fields
        project_field_names = {field.name.lower(): field.name for field in project.custom_fields}
        
        for csv_key, csv_value in row_data.items():
            csv_key_lower = csv_key.lower()
            
            # Skip if it's a standard field or empty
            if csv_key_lower in ["title", "description", "assignee", "labels", "status", "column", "project_status"]:
                continue
                
            if not csv_value or not csv_value.strip():
                continue
            
            # Check if this CSV column matches a project custom field
            if csv_key_lower in project_field_names:
                field_name = project_field_names[csv_key_lower]
                custom_fields[field_name] = csv_value.strip()
        
        return status, custom_fields
    
    def print_project_info(self, project: ProjectInfo) -> None:
        """Print detailed information about a project"""
        print(f"📋 Project: {project.title}")
        print(f"   URL: {project.url}")
        print(f"   Number: #{project.number}")
        
        if project.columns:
            print(f"   Columns: {', '.join([col.name for col in project.columns])}")
        
        if project.custom_fields:
            print("   Custom Fields:")
            for field in project.custom_fields:
                field_info = f"     • {field.name} ({field.data_type})"
                if field.options:
                    field_info += f" - Options: {', '.join(field.options)}"
                print(field_info)


# Example usage
if __name__ == "__main__":
    # This would be used for testing
    # from github import Github
    # github = Github("token")
    # repo = github.get_repo("owner/repo")
    # projects_client = GitHubProjectsClient(github, repo)
    # projects = projects_client.get_projects()
    pass



