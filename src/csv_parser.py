import pandas as pd
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class IssueData:
    """Represents a single GitHub issue from CSV data"""
    title: str
    description: str
    assignee: Optional[str] = None
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


class CSVParser:
    """Flexible CSV parser for GitHub issues"""
    
    # Define flexible column mappings - handles variations in naming
    COLUMN_MAPPINGS = {
        'title': ['issue title', 'title', 'issue', 'summary', 'name'],
        'description': ['description', 'desc', 'details', 'body', 'content'],
        'assignee': ['assignee', 'assigned to', 'owner', 'responsible'],
        'labels': ['label', 'labels', 'tags', 'category', 'type']
    }
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.df = None
        self.column_map = {}
    
    def parse(self) -> List[IssueData]:
        """Parse CSV file and return list of IssueData objects"""
        try:
            # Read CSV with flexible options
            self.df = pd.read_csv(
                self.csv_file_path,
                skipinitialspace=True,  # Remove leading whitespace
                na_filter=False  # Keep empty strings as empty, not NaN
            )
            
            # Clean column headers
            self.df.columns = self.df.columns.str.strip().str.lower()
            
            # Map columns to our standard fields
            self._map_columns()
            
            # Validate required columns exist
            self._validate_required_columns()
            
            # Convert to IssueData objects
            issues = []
            for _, row in self.df.iterrows():
                issue = self._row_to_issue(row)
                if issue:  # Skip invalid rows
                    issues.append(issue)
            
            return issues
            
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    def _map_columns(self) -> None:
        """Map CSV columns to our standard field names"""
        available_columns = set(self.df.columns)
        
        for field, possible_names in self.COLUMN_MAPPINGS.items():
            for possible_name in possible_names:
                if possible_name in available_columns:
                    self.column_map[field] = possible_name
                    break
    
    def _validate_required_columns(self) -> None:
        """Ensure required columns are present"""
        required_fields = ['title', 'description']
        missing_fields = []
        
        for field in required_fields:
            if field not in self.column_map:
                missing_fields.append(field)
        
        if missing_fields:
            available_cols = ', '.join(self.df.columns)
            raise ValueError(
                f"Missing required columns: {missing_fields}. "
                f"Available columns: {available_cols}"
            )
    
    def _row_to_issue(self, row: pd.Series) -> Optional[IssueData]:
        """Convert a DataFrame row to an IssueData object"""
        try:
            # Get title (required)
            title = self._get_field_value(row, 'title')
            if not title or title.strip() == '':
                print(f"Warning: Skipping row with empty title: {row.to_dict()}")
                return None
            
            # Get description (required)
            description = self._get_field_value(row, 'description')
            if not description:
                description = ''  # Allow empty descriptions
            
            # Get optional fields
            assignee = self._get_field_value(row, 'assignee')
            if assignee and assignee.strip() == '':
                assignee = None
                
            labels_raw = self._get_field_value(row, 'labels')
            labels = self._parse_labels(labels_raw)
            
            return IssueData(
                title=title.strip(),
                description=description.strip(),
                assignee=assignee.strip() if assignee else None,
                labels=labels
            )
            
        except Exception as e:
            print(f"Warning: Error processing row {row.to_dict()}: {str(e)}")
            return None
    
    def _get_field_value(self, row: pd.Series, field: str) -> Optional[str]:
        """Get field value from row using column mapping"""
        if field in self.column_map:
            column_name = self.column_map[field]
            value = row.get(column_name, '')
            return str(value) if pd.notna(value) and value != '' else None
        return None
    
    def _parse_labels(self, labels_raw: Optional[str]) -> List[str]:
        """Parse labels from string - handles comma, semicolon, or pipe separation"""
        if not labels_raw:
            return []
        
        # Split by common separators and clean up
        separators = [',', ';', '|']
        labels = [labels_raw]  # Start with original string
        
        for sep in separators:
            if sep in labels_raw:
                labels = labels_raw.split(sep)
                break
        
        # Clean and filter labels
        cleaned_labels = []
        for label in labels:
            label = label.strip()
            if label:  # Only add non-empty labels
                cleaned_labels.append(label)
        
        return cleaned_labels
    
    def get_column_mapping_info(self) -> Dict[str, str]:
        """Return information about how columns were mapped"""
        return self.column_map.copy()
    
    def preview_data(self, num_rows: int = 5) -> None:
        """Print a preview of parsed data for debugging"""
        if self.df is None:
            print("No data loaded. Run parse() first.")
            return
            
        print(f"CSV Columns Found: {list(self.df.columns)}")
        print(f"Column Mappings: {self.column_map}")
        print(f"\nFirst {num_rows} rows of data:")
        print(self.df.head(num_rows).to_string())


# Example usage and testing
if __name__ == "__main__":
    # This would be used to test the parser
    # parser = CSVParser("sample_issues.csv")
    # issues = parser.parse()
    # parser.preview_data()
    # 
    # for issue in issues:
    #     print(f"Title: {issue.title}")
    #     print(f"Description: {issue.description}")
    #     print(f"Assignee: {issue.assignee}")
    #     print(f"Labels: {issue.labels}")
    #     print("-" * 40)
    pass
