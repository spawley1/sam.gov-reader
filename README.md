# SAM.gov Contract Filter

## Description

The SAM.gov Contract Filter is a powerful desktop application designed to help users search, analyze, and manage government contract data from SAM.gov (System for Award Management). This tool provides an intuitive interface for filtering contracts, performing AI-enhanced searches using Claude AI, and exporting results in various formats.

## Features

- Load and parse SAM.gov CSV data files
- Basic and advanced search capabilities
- AI-enhanced searching and analysis using Claude AI
- Pagination for large result sets
- Bulk update and delete operations
- Export results in CSV, JSON, and Excel formats
- Entity extraction from contract data

## Requirements

- Python 3.7+
- PyQt5
- pandas
- openpyxl
- anthropic
- SQLite3 (usually comes with Python)

## Installation

1. Clone this repository or download the source code.
2. Install the required Python packages:

```
pip install PyQt5 pandas openpyxl anthropic
```

3. Ensure you have an Anthropic API key for Claude AI functionality.

## Usage

1. Run the application:

```
python main.py
```

2. Load a SAM.gov CSV file using the "Select CSV File" button.
3. Enter your Anthropic API key in the provided field and click "Set API Key".
4. Use the search tabs to filter contracts:
   - Basic Search: Keyword, date range, and agency selection
   - Advanced Search: NAICS code, contract value range, and performance location
5. Click "Search Contracts" to perform a search.
6. Use the "Use Claude AI" checkbox for AI-enhanced searching.
7. View results in the table, navigate through pages, and perform bulk operations as needed.
8. Export results using the export options at the bottom of the window.

## File Structure

- `main.py`: Main application file with GUI implementation
- `contract_database.py`: SQLite database operations for contract data
- `claude_search.py`: Implementation of Claude AI search capabilities
- `contracts.db`: SQLite database file (created when loading CSV data)

## Contributing

Contributions to improve the SAM.gov Contract Filter are welcome. Please fork the repository and submit a pull request with your changes.

## Disclaimer

This application is not officially affiliated with SAM.gov or any government agency. It is a third-party tool designed to assist with contract data analysis. Users are responsible for ensuring compliance with all applicable regulations when using this tool.

## Support

For issues, questions, or feature requests, please open an issue in the GitHub repository or contact [Your Contact Information].
