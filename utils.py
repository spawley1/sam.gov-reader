import logging
import json
from datetime import datetime
from typing import Any, Dict

def setup_logging(log_file: str = 'sam_contract_filter.log') -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_date(date_string: str) -> datetime:
    """Parse a date string into a datetime object."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        logging.warning(f"Invalid date format: {date_string}")
        return None

def format_currency(amount: float) -> str:
    """Format a float as a currency string."""
    return f"${amount:,.2f}"

def safe_json_loads(json_string: str) -> Dict[str, Any]:
    """Safely load a JSON string into a dictionary."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON: {json_string}")
        return {}

def sanitize_input(input_string: str) -> str:
    """Sanitize input string to prevent SQL injection."""
    return input_string.replace("'", "''")

def validate_contract_data(contract: Dict[str, Any]) -> bool:
    """Validate contract data to ensure all required fields are present."""
    required_fields = ['Notice ID', 'Title', 'Department/Ind. Agency', 'Date Posted']
    return all(field in contract for field in required_fields)

def create_search_query(search_params: Dict[str, Any]) -> str:
    """Create a SQL query string from search parameters."""
    conditions = []
    for key, value in search_params.items():
        if value:
            if isinstance(value, list):
                conditions.append(f"{key} IN ({','.join(['?']*len(value))})")
            else:
                conditions.append(f"{key} = ?")
    
    if conditions:
        return "WHERE " + " AND ".join(conditions)
    return ""

logger = setup_logging()
