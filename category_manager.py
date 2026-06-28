"""
category_manager.py
---------------------
Lets the user add their OWN custom categories (e.g. "Pet Care", "Subscriptions")
on top of the 12 ML-trained categories, and remembers which merchants they've
manually mapped to a category, so the same merchant is never asked about twice.

This does NOT retrain the ML model live (that would be slow and unnecessary
for a personal finance app). Instead:
  - Custom categories are stored separately (custom_categories.json)
  - User corrections/manual tags are remembered (user_category_rules.json)
  - Learned rules always win over the ML model's guess

In a real Flask app, swap the JSON file storage for `categories` and
`category_rules` SQL tables -- the logic stays identical.
"""

import json
import os
from datetime import datetime

CUSTOM_CATEGORIES_FILE = "custom_categories.json"
USER_RULES_FILE = "user_category_rules.json"

# The 12 categories the ML model was trained on.
BUILTIN_CATEGORIES = [
    "Food", "Transport", "Shopping", "Groceries", "Entertainment",
    "Bills & Utilities", "Healthcare", "Rent", "Education", "Travel",
    "Personal Care", "Salary",
]


class CategoryManager:
    """Manages custom categories and merchant -> category rules, persisted to JSON."""

    def __init__(self, categories_file=CUSTOM_CATEGORIES_FILE, rules_file=USER_RULES_FILE):
        self.categories_file = categories_file
        self.rules_file = rules_file
        self.custom_categories = self._load_json(categories_file, default=[])
        self.user_rules = self._load_json(rules_file, default=[])

    def _load_json(self, path, default):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def all_categories(self):
        """Built-in + custom category names combined."""
        return BUILTIN_CATEGORIES + [c["name"] for c in self.custom_categories]

    def ensure_category(self, name: str, category_type: str = "expense"):
        """
        Make sure a category exists -- add it if it's new, otherwise just
        return its name as-is. Never raises an error either way.
        """
        name = name.strip()
        if name.lower() in [c.lower() for c in self.all_categories()]:
            return name

        self.custom_categories.append({
            "name": name,
            "type": category_type,
            "created_at": datetime.now().isoformat(),
        })
        self._save_json(self.categories_file, self.custom_categories)
        return name

    def add_rule(self, merchant: str = None, keyword: str = None, category: str = None):
        """
        Remember that this merchant (or keyword) should always map to this
        category from now on. Replaces any existing rule for the same
        merchant/keyword instead of piling up duplicates.
        """
        if not merchant and not keyword:
            raise ValueError("Must provide at least a merchant or a keyword")
        if not category:
            raise ValueError("Must provide a category")

        rule = {
            "merchant": merchant.strip().lower() if merchant else None,
            "keyword": keyword.strip().lower() if keyword else None,
            "category": category,
        }
        self.user_rules = [
            r for r in self.user_rules
            if not (r["merchant"] == rule["merchant"] and r["keyword"] == rule["keyword"])
        ]
        self.user_rules.append(rule)
        self._save_json(self.rules_file, self.user_rules)
        return rule

    def match_rule(self, description: str, merchant: str = None):
        """
        Check if a previously learned rule matches this transaction.
        Returns the category name if matched, else None.
        Merchant match takes priority over keyword match.
        """
        merchant_lower = merchant.strip().lower() if merchant else ""
        description_lower = description.strip().lower() if description else ""

        for rule in self.user_rules:
            if rule["merchant"] and merchant_lower and rule["merchant"] == merchant_lower:
                return rule["category"]

        for rule in self.user_rules:
            if rule["keyword"] and rule["keyword"] in description_lower:
                return rule["category"]

        return None
