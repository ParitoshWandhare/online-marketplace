"""
Validation service for gift items to ensure data quality.
"""

import logging
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_items(items: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate items to ensure they have required fields.
    
    Args:
        items: List of items to validate
        
    Returns:
        Tuple containing:
        - List of valid items
        - List of invalid items with reasons
    """
    required_fields = ['title', 'description', 'category']
    valid_items = []
    invalid_items = []
    
    for item in items:
        missing_fields = []
        
        # Check required fields
        for field in required_fields:
            if field not in item or not item[field]:
                missing_fields.append(field)
        
        if missing_fields:
            invalid_reason = f"Missing fields: {', '.join(missing_fields)}"
            invalid_items.append({
                'item': item,
                'reason': invalid_reason
            })
            logger.warning(f"Invalid item: {invalid_reason}")
        else:
            valid_items.append(item)
    
    logger.info(f"Validation complete: {len(valid_items)} valid, {len(invalid_items)} invalid items")
    return valid_items, invalid_items