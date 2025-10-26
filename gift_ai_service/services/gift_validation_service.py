# # gift_ai_service/services/gift_validation_service.py
# from typing import List, Dict, Any, Tuple

# def validate_items(items: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
#     """
#     Validate items: price, availability, fraud
#     """
#     valid = []
#     invalid = []
    
#     for item in items:
#         if (item.get("price", 0) > 0 and 
#             item.get("in_stock", True) and 
#             item.get("fraud_score", 0) < 0.7):
#             valid.append(item)
#         else:
#             invalid.append(item)
    
#     return valid, invalid
# gift_ai_service/services/gift_validation_service.py
from typing import List, Dict, Tuple

def validate_items(items: List[Dict], max_budget: int = 1000) -> Tuple[List[Dict], List[Dict]]:
    valid = []
    invalid = []
    
    for item in items:
        price = item.get("price", 0)
        if (price <= max_budget and 
            item.get("in_stock", True) and 
            item.get("fraud_score", 0) < 0.7):
            valid.append(item)
        else:
            invalid.append(item)
    
    return valid, invalid