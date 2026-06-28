"""
categorizer.py
----------------
The single function your app should call to categorize any transaction.

Priority order (most trusted first):
  1. User-defined rule (merchant or keyword the user manually mapped before)
  2. ML model prediction (if confidence >= threshold)
  3. Simple keyword-based fallback
  4. "Uncategorized" (last resort -- shows up in UI for manual tagging)

This is the file to import from your Flask routes / CSV import logic.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.category_classifier import CategoryPredictor
from category_manager import CategoryManager

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trained_models", "category_classifier.pkl")

# Load once, reuse everywhere (don't reload these inside a loop or per-request)
_predictor = None
_category_manager = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = CategoryPredictor(MODEL_PATH)
    return _predictor


def get_category_manager():
    global _category_manager
    if _category_manager is None:
        _category_manager = CategoryManager()
    return _category_manager


def rule_based_categorize(description: str, merchant: str = None) -> str:
    """Simple keyword fallback for the 12 built-in categories.
    Only used when neither a user rule nor the ML model are confident."""
    text = (description or "") + " " + (merchant or "")
    text = text.lower()

    keyword_map = {
        "Food": ["swiggy", "zomato", "restaurant", "cafe", "dominos", "kfc", "starbucks"],
        "Transport": ["uber", "ola", "rapido", "petrol", "fuel", "metro", "irctc"],
        "Shopping": ["amazon", "flipkart", "myntra", "ajio", "croma"],
        "Groceries": ["bigbasket", "dmart", "blinkit", "zepto", "kirana"],
        "Entertainment": ["netflix", "prime", "bookmyshow", "spotify", "hotstar"],
        "Bills & Utilities": ["electricity", "airtel", "jio", "vodafone", "water board", "gas"],
        "Healthcare": ["pharmacy", "hospital", "clinic", "medplus", "apollo"],
        "Rent": ["rent", "landlord", "housing society"],
        "Education": ["udemy", "coursera", "byju", "tuition", "school fee"],
        "Travel": ["makemytrip", "indigo", "oyo", "airbnb", "goibibo"],
        "Personal Care": ["salon", "urban company", "gym", "cult.fit"],
        "Salary": ["salary", "payroll"],
    }

    for category, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            return category

    return "Uncategorized"


def categorize_transaction(description: str, merchant: str = None, amount: float = None):
    """
    Main entry point. Returns a dict with the predicted category and
    metadata about HOW it was decided -- useful for showing the user
    "predicted automatically" vs "matched your rule" in the UI.
    """
    manager = get_category_manager()
    predictor = get_predictor()

    # 1. Check user-defined rules first -- these always win
    rule_match = manager.match_rule(description, merchant)
    if rule_match:
        return {
            "category": rule_match,
            "confidence": 1.0,
            "source": "user_rule",
        }

    # 2. ML model prediction
    category, confidence = predictor.predict(description, merchant=merchant, amount=amount)
    if category:
        return {
            "category": category,
            "confidence": confidence,
            "source": "ml_model",
        }

    # 3. Keyword fallback (covers built-in categories only)
    fallback_category = rule_based_categorize(description, merchant)
    return {
        "category": fallback_category,
        "confidence": confidence,  # the low ML confidence, for transparency
        "source": "rule_fallback" if fallback_category != "Uncategorized" else "uncategorized",
    }


def add_custom_category(name: str, category_type: str = "expense"):
    """
    Call this when the user clicks "Add Category" in the UI.
    category_type is 'expense' or 'income'.
    """
    manager = get_category_manager()
    return manager.add_category(name, category_type)


def assign_category_manually(description: str, category: str, merchant: str = None):
    """
    Call this when the user manually picks/corrects a category for a
    transaction (whether it's a custom category or a built-in one).
    This teaches the system to remember it -- next time the same
    merchant/description pattern appears, it'll use this category
    instead of asking the ML model or falling back to keywords.

    If `category` doesn't exist yet (built-in or custom), it's created
    automatically as a new custom category (default type: expense).
    """
    manager = get_category_manager()

    if category not in manager.all_categories():
        manager.add_category(category, category_type="expense")

    # Prefer remembering by merchant (more reliable); fall back to a
    # keyword from the description if no merchant is given.
    if merchant:
        manager.add_rule(merchant=merchant, category=category)
    else:
        # use the first significant word of the description as a keyword
        words = [w for w in description.lower().split() if len(w) > 3]
        keyword = words[0] if words else description.lower()
        manager.add_rule(keyword=keyword, category=category)


if __name__ == "__main__":
    # Quick demo of the whole flow
    print("=== Step 1: Add a custom category ===")
    add_custom_category("Pet Care", category_type="expense")
    add_custom_category("Freelance Income", category_type="income")

    print("\n=== Step 2: Categorize a transaction BEFORE teaching a rule ===")
    result = categorize_transaction("Petsy Mart dog food order", merchant="Petsy Mart", amount=850)
    print(result)  # ML model has never seen "Pet Care" -- falls back to Uncategorized

    print("\n=== Step 3: User manually assigns it to the new custom category ===")
    assign_category_manually("Petsy Mart dog food order", category="Pet Care", merchant="Petsy Mart")

    print("\n=== Step 4: Categorize the SAME merchant again -- should now use the rule ===")
    result = categorize_transaction("Petsy Mart dog food order", merchant="Petsy Mart", amount=850)
    print(result)

    print("\n=== Step 5: A normal built-in category still works via ML ===")
    result = categorize_transaction("Swiggy order #123", merchant="Swiggy", amount=400)
    print(result)

    print("\n=== All available categories (built-in + custom) ===")
    print(get_category_manager().all_categories())
