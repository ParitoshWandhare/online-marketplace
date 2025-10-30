# gift_ai_service/services/gift_validation_service.py
"""
Validation service for gift items to ensure data quality and budget compliance.
FIXED: More lenient defaults and better field checking
"""

import logging
from typing import List, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_items(
    items: List[Dict],
    max_budget: float = None,
    min_quality_score: float = 0.0  # Changed from 0.5 to 0.0 to be more lenient
) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate items to ensure they meet requirements.
    
    Args:
        items: List of items to validate
        max_budget: Maximum budget per item (INR)
        min_quality_score: Minimum similarity/quality score (0.0 = accept all)
        
    Returns:
        Tuple containing:
        - List of valid items
        - List of invalid items with reasons
    """
    required_fields = ['title']  # Only title is truly required
    valid_items = []
    invalid_items = []
    
    logger.info(f"🔍 Validating {len(items)} items")
    logger.info(f"   Max budget: {f'₹{max_budget}' if max_budget else 'None'}")
    logger.info(f"   Min score: {min_quality_score}")
    
    for idx, item in enumerate(items, 1):
        reasons = []
        
        # Get fields (already at root level from vector_store)
        title = item.get('title', '').strip()
        description = item.get('description', '').strip()
        price = item.get('price', 0)
        score = item.get('score', 1.0)
        
        # Check required fields
        if not title:
            reasons.append("Missing title")
        
        # Description is optional but warn if missing
        if not description:
            logger.debug(f"Item '{title}' has no description (non-critical)")
        
        # Check budget (only if max_budget is specified)
        if max_budget is not None and max_budget > 0:
            try:
                price_float = float(price)
                if price_float > max_budget:
                    reasons.append(f"Price ₹{price_float:.2f} exceeds budget ₹{max_budget:.2f}")
            except (ValueError, TypeError):
                reasons.append(f"Invalid price format: {price}")
        
        # Check quality score (only if threshold is set)
        if min_quality_score > 0:
            try:
                score_float = float(score)
                if score_float < min_quality_score:
                    reasons.append(f"Score {score_float:.2f} below threshold {min_quality_score:.2f}")
            except (ValueError, TypeError):
                pass  # Don't reject for invalid score
        
        # Categorize
        if reasons:
            invalid_items.append({
                'item': item,
                'reason': '; '.join(reasons)
            })
            logger.info(f"   [{idx}] ❌ INVALID: {title or 'Unknown'} - {', '.join(reasons)}")
        else:
            valid_items.append(item)
            logger.info(f"   [{idx}] ✅ VALID: {title} (₹{price}, score: {score:.3f})")
    
    logger.info(f"📊 Validation complete: {len(valid_items)} valid, {len(invalid_items)} invalid items")
    
    return valid_items, invalid_items