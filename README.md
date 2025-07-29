# Tissue

A command-line tool for creating GitHub issues within the terminal (hence T(erminal)issue) from CSV files. Tissue makes it easy to bulk-import issues, feature requests, and bug reports into your GitHub repositories.

## Features

- **Flexible CSV parsing** - Works with various column names and formats
- **Smart duplicate detection** - Skips issues with identical titles
- **Automatic label creation** - Creates missing labels in your repository
- **Assignee validation** - Warns about invalid assignees but continues processing
- **Robust error handling** - Continues processing even if individual issues fail
- **Multiple output modes** - Verbose, normal, and quiet modes
- **Comprehensive validation** - Validates repository format, file existence, and CSV structure

## Installation

### From Source

```bash
git clone https://github.com/ryansweigart3/tissue.git
cd tissue
pip install -e .
```

### Using pip (when published)

```bash
pip install tissue
```

## Quick Start

1. **Create a CSV file** with your issues (see [CSV Format](#csv-format) below)
2. **Get a GitHub token** with repo permissions
3. **Run tissue**:

```bash
tissue --file issues.csv --repo owner/repository --token ghp_your_token_here
```

## CSV Format

Tissue accepts flexible CSV formats. The following column names are supported:

| Field | Accepted Column Names | Required | Description |
|-------|----------------------|----------|-------------|
| Title | `issue title`, `title`, `issue`, `summary`, `name` | ✅ | The issue title |
| Description | `description`, `desc`, `details`, `body`, `content` | ✅ | The issue description/body |
| Assignee | `assignee`, `assigned to`, `owner`, `responsible` | ❌ | GitHub username to assign |
| Labels | `label`, `labels`, `tags`, `category`, `type` | ❌ | Labels (comma/semicolon/pipe separated) |

### Example CSV

```csv
issue title,description,assignee,label
Fix login bug,Users can't log in with special characters,john_doe,bug;high-priority
Add dark mode,Implement dark theme for better UX,jane_smith,enhancement
Update docs,Fix typos in README,,documentation,low-priority
```

## Usage

### Basic Usage

```bash
tissue --file issues.csv --repo myorg/myproject --token ghp_xxxxxxxxxxxx
```

### Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--file` | `-f` | Path to CSV file (required) |
| `--repo` | `-r` | GitHub repository in `owner/repo` format (required) |
| `--token` | `-t` | GitHub personal access token (required) |
| `--verbose` | `-v` | Show detailed progress information |
| `--quiet` | `-q` | Show only final summary and errors |
| `--help` | `-h` | Show help message |
| `--version` |  | Show version information |

### Examples

**Verbose output:**
```bash
tissue -f issues.csv -r myorg/myproject -t ghp_xxx --verbose
```

**Quiet mode:**
```bash
tissue -f issues.csv -r myorg/myproject -t ghp_xxx --quiet
```

**Get help:**
```bash
tissue --help
```

## GitHub Token Setup

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the `repo` scope (Full control of private repositories)
4. Copy the generated token (starts with `ghp_`)

**⚠️ Keep your token secure and never commit it to version control!**

## How It Works

1. **CSV Parsing**: Tissue reads your CSV file and maps columns to issue fields using flexible name matching
2. **GitHub Connection**: Connects to GitHub and validates repository access
3. **Duplicate Check**: Checks for existing issues with the same title to avoid duplicates
4. **Label Management**: Creates any missing labels in your repository
5. **Assignee Validation**: Verifies assignees have repository access (warns if not)
6. **Issue Creation**: Creates issues with proper error handling and progress reporting

## Error Handling

Tissue is designed to be robust:

- **Invalid assignees**: Warns but creates issue without assignee
- **Missing labels**: Automatically creates labels with default styling
- **Duplicate titles**: Skips duplicate issues and reports them
- **Individual failures**: Continues processing remaining issues if one fails
- **Network issues**: Provides clear error messages and appropriate exit codes

## Output Examples

### Successful Run
```
Parsing CSV file...
Successfully parsed 3 issues from CSV
Connecting to GitHub...
Connected to GitHub as: yourusername
Repository: yourusername/test-repo
Caching existing issues...
Found 5 existing open issues
Caching existing labels...
Found 8 existing labels
Starting batch creation of 3 issues...
Processing issue 1/3: Fix login bug
  ✓ Created: https://github.com/yourusername/test-repo/issues/123
Processing issue 2/3: Add dark mode
  Created new label: 'enhancement'
  ✓ Created: https://github.com/yourusername/test-repo/issues/124
Processing issue 3/3: Update documentation
  ⊝ Skipped: Issue with title 'Update documentation' already exists

============================================================
BATCH ISSUE CREATION SUMMARY
============================================================
Total issues processed: 3
Successfully created:   2
Skipped (duplicates):   1
Failed:                 0
============================================================

✓ Successfully created 2 issues!
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Project Structure

```
tissue/
├── src/
│   ├── __init__.py
│   ├── main.py           # CLI interface
│   ├── csv_parser.py     # CSV parsing logic
│   └── github_client.py  # GitHub API integration
├── tests/
│   ├── __init__.py
│   └── test_csv_parser.py
├── requirements.txt
├── setup.py
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/tissue/issues) page
2. Create a new issue with:
   - Your CSV file format (with sensitive data removed)
   - The exact command you ran
   - The error message or unexpected behavior
   - Your Python and tissue version

## Changelog

### v1.0.0
- Initial release
- CSV parsing with flexible column mapping
- GitHub issue creation with labels and assignees
- Duplicate detection and error handling
- Verbose and quiet output modes
