# gift_ai_service/services/gift_validation_service.py
"""
Validation service for gift items to ensure data quality and budget compliance.
"""

import logging
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_items(
    items: List[Dict],
    max_budget: float = None,
    min_quality_score: float = 0.5
) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate items to ensure they meet requirements.
    
    Args:
        items: List of items to validate
        max_budget: Maximum budget per item (INR)
        min_quality_score: Minimum similarity/quality score
        
    Returns:
        Tuple containing:
        - List of valid items
        - List of invalid items with reasons
    """
    required_fields = ['title', 'description']
    valid_items = []
    invalid_items = []
    
    for item in items:
        reasons = []
        
        # Check required fields
        missing_fields = [f for f in required_fields if f not in item or not item[f]]
        if missing_fields:
            reasons.append(f"Missing fields: {', '.join(missing_fields)}")
        
        # Check budget
        if max_budget and item.get('price', 0) > max_budget:
            reasons.append(f"Price ₹{item.get('price', 0)} exceeds budget ₹{max_budget}")
        
        # Check quality score
        if min_quality_score and item.get('score', 1.0) < min_quality_score:
            reasons.append(f"Quality score {item.get('score', 0)} below threshold {min_quality_score}")
        
        # Categorize
        if reasons:
            invalid_items.append({
                'item': item,
                'reason': '; '.join(reasons)
            })
            logger.debug(f"❌ Invalid item: {item.get('title', 'Unknown')} - {reasons}")
        else:
            valid_items.append(item)
    
    logger.info(f"✅ Validation complete: {len(valid_items)} valid, {len(invalid_items)} invalid items")
    return valid_items, invalid_items