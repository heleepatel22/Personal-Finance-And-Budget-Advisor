"""
interactive_categorizer.py
----------------------------
Interactive command-line tool to test the FULL categorization system:
  - ML model predictions
  - User-defined custom categories
  - User correction rules (merchant -> category memory)

Run:
    python interactive_categorizer.py

Menu-driven -- no need to remember function names.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from categorizer import (
    categorize_transaction,
    add_custom_category,
    assign_category_manually,
    get_category_manager,
)


def print_menu():
    print()
    print("=" * 60)
    print("1. Categorize a transaction")
    print("2. Add a custom category")
    print("3. Correct/assign a category manually (teaches the system)")
    print("4. List all categories (built-in + custom)")
    print("5. List learned rules")
    print("6. Exit")
    print("=" * 60)


def handle_categorize():
    desc = input("Description: ").strip()
    merch = input("Merchant (optional): ").strip() or None
    amt_str = input("Amount (optional): ").strip()
    amt = float(amt_str) if amt_str else None

    result = categorize_transaction(desc, merchant=merch, amount=amt)
    print()
    print(f"  Category   : {result['category']}")
    print(f"  Confidence : {result['confidence']:.2%}")
    print(f"  Source     : {result['source']}  "
          f"({'matched your rule' if result['source']=='user_rule' else result['source']})")

    print()
    fix = input("  Is this correct? Press Enter to accept, or type 'n' to fix it: ").strip().lower()
    if fix == "n":
        cat = input("  Which category should this actually be? (can be a new or existing category): ").strip()
        assign_category_manually(desc, category=cat, merchant=merch)
        print(f"  Got it -- '{merch or desc}' will be categorized as '{cat}' from now on.")


def handle_add_category():
    name = input("New category name (e.g. 'Pet Care'): ").strip()
    ctype = input("Type -- expense or income? [expense]: ").strip().lower() or "expense"
    try:
        add_custom_category(name, category_type=ctype)
    except ValueError as e:
        print(f"  Error: {e}")


def handle_assign_manually():
    desc = input("Transaction description: ").strip()
    merch = input("Merchant (optional, recommended): ").strip() or None
    cat = input("Category to assign: ").strip()
    assign_category_manually(desc, category=cat, merchant=merch)


def handle_list_categories():
    manager = get_category_manager()
    print("\nBuilt-in + custom categories:")
    for c in manager.all_categories():
        tag = " (custom)" if c not in manager.all_categories()[:12] else ""
        print(f"  - {c}{tag}")


def handle_list_rules():
    manager = get_category_manager()
    rules = manager.list_rules()
    if not rules:
        print("\nNo rules learned yet.")
        return
    print(f"\n{len(rules)} learned rule(s):")
    for r in rules:
        key = r["merchant"] or r["keyword"]
        key_type = "merchant" if r["merchant"] else "keyword"
        print(f"  - {key_type}='{key}'  ->  {r['category']}")


if __name__ == "__main__":
    print("Personal Finance Categorizer -- Interactive Test Tool")

    actions = {
        "1": handle_categorize,
        "2": handle_add_category,
        "3": handle_assign_manually,
        "4": handle_list_categories,
        "5": handle_list_rules,
    }

    while True:
        print_menu()
        choice = input("Choose an option (1-6): ").strip()

        if choice == "6":
            print("Goodbye.")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice, try again.")
