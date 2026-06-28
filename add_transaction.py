"""
add_transaction.py
---------------------
Simple way to add a transaction: description, merchant, amount, category.

Rules:
  - If category already exists (built-in or custom) -> just use it, no error.
  - If category is left blank -> predict it using the ML model, and tell
    the user what was predicted.
  - If category is new -> it's added automatically, no error/announcement.
  - Every transaction gets appended to the growing dataset so the model
    can be retrained on it later (transactions_dataset.csv).
  - Always ends with a clean confirmation message. No tracebacks, no
    confidence numbers, no extra noise.

Run:
    python add_transaction.py
"""

import sys
import os
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from category_manager import CategoryManager
from ml.category_classifier import CategoryPredictor

DATASET_FILE = "transactions_dataset.csv"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trained_models", "category_classifier.pkl")
DATASET_COLUMNS = ["date", "description", "merchant", "amount", "category"]

_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = CategoryPredictor(MODEL_PATH)
    return _predictor


def append_to_dataset(row: dict):
    """Append one transaction to the growing CSV dataset, creating the
    file with a header the first time it's used."""
    file_exists = os.path.exists(DATASET_FILE)
    with open(DATASET_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DATASET_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def add_transaction():
    description = input("Description: ").strip()
    merchant = input("Merchant: ").strip()
    amount = input("Amount: ").strip()
    category = input("Category (leave blank to auto-predict): ").strip()

    amount_value = float(amount) if amount else 0.0
    predicted = False
    manager = CategoryManager()

    if category:
        # Make sure it exists -- silently reuse if it's already there,
        # silently create it if it's new. Never errors either way.
        category = manager.ensure_category(category, category_type="expense")
    else:
        # No category given. Check what we've LEARNED before first --
        # if this merchant (or a matching keyword) was taught before,
        # use that instead of asking the ML model again.
        learned_category = manager.match_rule(description, merchant)
        if learned_category:
            category = learned_category
            predicted = True  # still show it to the user, just like an ML prediction
        else:
            # Genuinely new -- predict it with the ML model.
            predictor = get_predictor()
            predicted_category, confidence = predictor.predict(description, merchant=merchant, amount=amount_value)
            category = predicted_category or "Uncategorized"
            predicted = True

    # Remember merchant -> category for next time (only if a real merchant given)
    if merchant and category != "Uncategorized":
        manager.add_rule(merchant=merchant, category=category)

    # Save to the growing dataset so the model can be retrained on this later
    append_to_dataset({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": description,
        "merchant": merchant,
        "amount": amount_value,
        "category": category,
    })

    print()
    if predicted:
        print(f"Predicted category: {category}")
    print("Data added, thank you.")


if __name__ == "__main__":
    while True:
        add_transaction()
        print()
        again = input("Add another? (y/n): ").strip().lower()
        if again != "y":
            break
