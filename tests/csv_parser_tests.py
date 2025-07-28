import unittest
import tempfile
import os
import pandas as pd
from src.csv_parser import CSVParser, IssueData


class TestCSVParser(unittest.TestCase):
    """Test suite for CSVParser class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.temp_files = []
    
    def tearDown(self):
        """Clean up temporary files after each test"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def create_temp_csv(self, content: str) -> str:
        """Helper method to create temporary CSV files for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def test_basic_parsing(self):
        """Test basic CSV parsing with standard headers"""
        csv_content = """issue title,description,assignee,label
Fix login bug,Users can't log in with special characters,john_doe,bug
Add dark mode,Implement dark theme for better UX,jane_smith,enhancement
Update docs,Fix typos in README,,documentation"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        self.assertEqual(len(issues), 3)
        
        # Test first issue
        self.assertEqual(issues[0].title, "Fix login bug")
        self.assertEqual(issues[0].description, "Users can't log in with special characters")
        self.assertEqual(issues[0].assignee, "john_doe")
        self.assertEqual(issues[0].labels, ["bug"])
        
        # Test second issue
        self.assertEqual(issues[1].title, "Add dark mode")
        self.assertEqual(issues[1].assignee, "jane_smith")
        self.assertEqual(issues[1].labels, ["enhancement"])
        
        # Test third issue (no assignee)
        self.assertEqual(issues[2].title, "Update docs")
        self.assertIsNone(issues[2].assignee)
        self.assertEqual(issues[2].labels, ["documentation"])
    
    def test_flexible_column_names(self):
        """Test that parser handles different column name variations"""
        csv_content = """Title,Desc,Assigned To,Tags
Bug in search,Search returns wrong results,alice,bug;critical
New feature request,Add export functionality,bob,enhancement"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0].title, "Bug in search")
        self.assertEqual(issues[0].description, "Search returns wrong results")
        self.assertEqual(issues[0].assignee, "alice")
        self.assertEqual(issues[0].labels, ["bug", "critical"])
    
    def test_multiple_label_separators(self):
        """Test parsing labels with different separators"""
        csv_content = """issue title,description,assignee,label
Issue 1,Description 1,user1,"bug,high-priority"
Issue 2,Description 2,user2,enhancement;ui;frontend
Issue 3,Description 3,user3,documentation|help-wanted"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0].labels, ["bug", "high-priority"])
        self.assertEqual(issues[1].labels, ["enhancement", "ui", "frontend"])
        self.assertEqual(issues[2].labels, ["documentation", "help-wanted"])
    
    def test_whitespace_handling(self):
        """Test that parser properly handles whitespace in headers and data"""
        csv_content = """  Issue Title  ,  Description  ,  Assignee  ,  Label  
  Fix bug  ,  Remove extra spaces  ,  john  ,  bug  
Another issue,Normal description,jane,enhancement"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0].title, "Fix bug")
        self.assertEqual(issues[0].description, "Remove extra spaces")
        self.assertEqual(issues[0].assignee, "john")
        self.assertEqual(issues[0].labels, ["bug"])
    
    def test_empty_values_handling(self):
        """Test handling of empty and missing values"""
        csv_content = """issue title,description,assignee,label
Valid issue,This has all fields,user1,bug
No assignee,This has no assignee,,enhancement
Empty description,,user2,documentation
,Missing title,user3,bug"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        # Should only get 3 issues (row with missing title should be skipped)
        self.assertEqual(len(issues), 3)
        
        # Test no assignee
        self.assertEqual(issues[1].title, "No assignee")
        self.assertIsNone(issues[1].assignee)
        
        # Test empty description
        self.assertEqual(issues[2].title, "Empty description")
        self.assertEqual(issues[2].description, "")
    
    def test_missing_required_columns(self):
        """Test error handling when required columns are missing"""
        csv_content = """summary,details,owner
Some issue,Some description,some_user"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        
        with self.assertRaises(ValueError) as context:
            parser.parse()
        
        self.assertIn("Missing required columns", str(context.exception))
    
    def test_empty_csv_file(self):
        """Test handling of empty CSV file"""
        csv_content = ""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        
        with self.assertRaises(ValueError):
            parser.parse()
    
    def test_only_headers_csv(self):
        """Test CSV file with only headers and no data"""
        csv_content = "issue title,description,assignee,label"
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        self.assertEqual(len(issues), 0)
    
    def test_column_mapping_info(self):
        """Test that column mapping information is correctly returned"""
        csv_content = """Title,Desc,Owner,Tags
Test issue,Test description,test_user,test_tag"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        parser.parse()
        
        mapping = parser.get_column_mapping_info()
        
        self.assertEqual(mapping['title'], 'title')
        self.assertEqual(mapping['description'], 'desc')
        self.assertEqual(mapping['assignee'], 'owner')
        self.assertEqual(mapping['labels'], 'tags')
    
    def test_invalid_file_path(self):
        """Test error handling for non-existent file"""
        parser = CSVParser("non_existent_file.csv")
        
        with self.assertRaises(ValueError) as context:
            parser.parse()
        
        self.assertIn("Error parsing CSV file", str(context.exception))
    
    def test_malformed_csv(self):
        """Test handling of malformed CSV data"""
        csv_content = """issue title,description,assignee,label
"Unclosed quote,This should cause issues,user1,bug
Normal row,This should work,user2,enhancement"""
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        
        # Should handle malformed CSV gracefully
        try:
            issues = parser.parse()
            # At least one valid row should be parsed
            self.assertGreaterEqual(len(issues), 1)
        except ValueError:
            # Or it should raise a clear error
            pass
    
    def test_issue_data_class(self):
        """Test IssueData dataclass functionality"""
        # Test with all fields
        issue1 = IssueData(
            title="Test Issue",
            description="Test Description",
            assignee="test_user",
            labels=["bug", "critical"]
        )
        
        self.assertEqual(issue1.title, "Test Issue")
        self.assertEqual(issue1.description, "Test Description")
        self.assertEqual(issue1.assignee, "test_user")
        self.assertEqual(issue1.labels, ["bug", "critical"])
        
        # Test with minimal fields (labels should default to empty list)
        issue2 = IssueData(
            title="Minimal Issue",
            description="Minimal Description"
        )
        
        self.assertEqual(issue2.labels, [])
        self.assertIsNone(issue2.assignee)
    
    def test_special_characters_in_data(self):
        """Test handling of special characters in CSV data"""
        csv_content = csv_content = '''issue title,description,assignee,label
"Issue with ""quotes""","Description with, commas and ""quotes""",user@domain.com,bug
Issue with newlines,"This description has actual newlines in it",user_name,enhancement
Unicode issue,Description with émojis 🐛 and ñoñó,тест_user,i18n'''
        
        csv_file = self.create_temp_csv(csv_content)
        parser = CSVParser(csv_file)
        issues = parser.parse()
        
        self.assertEqual(len(issues), 3)
        
        # Test quotes handling
        self.assertEqual(issues[0].title, 'Issue with "quotes"')
        self.assertIn('commas and "quotes"', issues[0].description)
        
        # Test unicode
        self.assertEqual(issues[2].assignee, "тест_user")
        self.assertIn("émojis 🐛", issues[2].description)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
