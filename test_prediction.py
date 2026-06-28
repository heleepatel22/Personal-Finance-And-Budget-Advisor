"""
test_prediction.py
--------------------
A small, standalone script to check whether the trained category classifier
is giving correct predictions. No Flask, no database -- just load the model
and test it.

Run:
    python test_prediction.py

Two modes:
  1. Runs a fixed batch of sample transactions automatically (always runs)
  2. Then drops you into an interactive prompt where YOU can type any
     description/merchant/amount and see the live prediction
"""

import sys
import os

# Make sure we can import ml/category_classifier.py from this folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.category_classifier import CategoryPredictor

MODEL_PATH = "trained_models/category_classifier.pkl"


def run_sample_batch(predictor):
    print("=" * 70)
    print("BATCH TEST -- checking the model against known sample transactions")
    print("=" * 70)

    # (description, merchant, amount, expected_category)
    # expected_category is just OUR guess of what it SHOULD predict --
    # use this to eyeball whether the model is sane, not as ground truth.
    samples = [
        ("Swiggy order #4521", "Swiggy", 450.0, "Food"),
        ("Uber trip to airport", "Uber", 650.0, "Transport"),
        ("NEFT salary credit June", "Employer Pvt Ltd", 55000.0, "Salary"),
        ("Amazon purchase - electronics", "Amazon", 3200.0, "Shopping"),
        ("BigBasket grocery order", "BigBasket", 1800.0, "Groceries"),
        ("Netflix monthly subscription", "Netflix", 199.0, "Entertainment"),
        ("Airtel postpaid bill payment", "Airtel", 599.0, "Bills & Utilities"),
        ("Apollo Pharmacy medicines", "Apollo Pharmacy", 450.0, "Healthcare"),
        ("Monthly rent payment", None, 15000.0, "Rent"),
        ("Udemy course purchase", "Udemy", 499.0, "Education"),
        ("MakeMyTrip flight booking", "MakeMyTrip", 8500.0, "Travel"),
        ("Urban Company salon service", "Urban Company", 800.0, "Personal Care"),
        ("asdkjaskjd random gibberish text", None, 120.0, "? (should be low confidence)"),
        ("NEFT/HDFC0001234/SALARY/JUNE", "Employer", 60000.0, "Salary (tricky format)"),
    ]

    correct = 0
    checkable = 0

    for desc, merch, amt, expected in samples:
        category, confidence = predictor.predict(desc, merchant=merch, amount=amt)
        result_str = category if category else "None (low confidence -> fallback)"

        # only auto-check the ones with a clean expected label
        is_checkable = "?" not in expected and "tricky" not in expected
        match_marker = ""
        if is_checkable:
            checkable += 1
            if category == expected:
                correct += 1
                match_marker = " ✅"
            else:
                match_marker = f" ❌ (expected {expected})"

        print(f"  '{desc[:40]:40}' merchant={str(merch):18} -> {result_str:20} (conf: {confidence:.2f}){match_marker}")

    print()
    print(f"Score on checkable samples: {correct}/{checkable} correct")
    print()


def run_unlabeled_csv_test(predictor):
    csv_path = "expense_unlabeled_for_prediction.csv"
    if not os.path.exists(csv_path):
        return

    import pandas as pd
    df = pd.read_csv(csv_path)

    print("=" * 70)
    print(f"CSV TEST -- predicting categories for {len(df)} real unlabeled rows")
    print("=" * 70)

    for _, row in df.head(10).iterrows():
        category, confidence = predictor.predict(row.get("description"), row.get("merchant"))
        result_str = category if category else "None -> fallback"
        print(f"  '{str(row.get('description'))[:40]:40}' -> {result_str:20} (conf: {confidence:.2f})")
    print(f"  ... ({len(df)} total rows in file)")
    print()


def interactive_mode(predictor):
    print("=" * 70)
    print("INTERACTIVE MODE -- type your own transactions to test")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 70)

    while True:
        print()
        desc = input("Description (e.g. 'Swiggy order'): ").strip()
        if desc.lower() in ("quit", "exit", ""):
            print("Exiting interactive mode.")
            break

        merch = input("Merchant (optional, press Enter to skip): ").strip() or None

        amt_input = input("Amount (optional, press Enter to skip): ").strip()
        amt = None
        if amt_input:
            try:
                amt = float(amt_input)
            except ValueError:
                print("  (invalid amount, ignoring)")

        category, confidence = predictor.predict(desc, merchant=merch, amount=amt)

        if category:
            print(f"  -> Predicted category: {category}  (confidence: {confidence:.2%})")
        else:
            print(f"  -> Model not confident (confidence: {confidence:.2%}) -- would fall back to rule-based categorizer")


if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: No trained model found at '{MODEL_PATH}'")
        print("Run 'python ml/category_classifier.py' first to train and save the model.")
        sys.exit(1)

    print("Loading trained model...")
    predictor = CategoryPredictor(MODEL_PATH)
    print(f"Model loaded. Knows {len(predictor.classes_)} categories: {list(predictor.classes_)}")
    print()
    print("NOTE: This script tests the raw ML model only (no custom categories,")
    print("no user rules). To test the FULL system -- including adding your own")
    print("categories and teaching it merchant rules -- run 'python categorizer.py'")
    print("or 'python interactive_categorizer.py' instead.")
    print()

    run_sample_batch(predictor)
    run_unlabeled_csv_test(predictor)
    interactive_mode(predictor)
