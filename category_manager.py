"""
category_manager.py
---------------------
Lets the user add their OWN custom categories (e.g. "Pet Care", "Subscriptions")
on top of the 12 ML-trained categories, and remembers which merchants/keywords
they've manually mapped to those custom categories.

This does NOT retrain the ML model live (that would be slow and unnecessary
for a personal finance app). Instead:
  - Custom categories are stored separately (custom_categories.json)
  - User corrections/manual tags are remembered (user_category_rules.json)
  - When predicting, USER RULES ALWAYS WIN over the ML model's guess

In your real Flask app, swap the JSON file storage for your `categories`
and `category_rules` SQL tables -- the logic stays identical.
"""

import json
import os
from datetime import datetime

CUSTOM_CATEGORIES_FILE = "custom_categories.json"
USER_RULES_FILE = "user_category_rules.json"

# The 12 categories the ML model was trained on -- used to block duplicates
# and to clearly separate "built-in" vs "custom" categories in the UI.
BUILTIN_CATEGORIES = [
    "Food", "Transport", "Shopping", "Groceries", "Entertainment",
    "Bills & Utilities", "Healthcare", "Rent", "Education", "Travel",
    "Personal Care", "Salary",
]


class CategoryManager:
    """
    Manages user-created custom categories and user-defined keyword/merchant
    -> category rules. Persists to JSON files so they survive between runs.
    """

    def __init__(self, categories_file=CUSTOM_CATEGORIES_FILE, rules_file=USER_RULES_FILE):
        self.categories_file = categories_file
        self.rules_file = rules_file
        self.custom_categories = self._load_json(categories_file, default=[])
        self.user_rules = self._load_json(rules_file, default=[])

    # -----------------------------------------------------------------
    # Persistence helpers
    # -----------------------------------------------------------------
    def _load_json(self, path, default):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _save_categories(self):
        self._save_json(self.categories_file, self.custom_categories)

    def _save_rules(self):
        self._save_json(self.rules_file, self.user_rules)

    # -----------------------------------------------------------------
    # Category management
    # -----------------------------------------------------------------
    def all_categories(self):
        """Returns built-in + custom category names combined (for dropdowns in UI)."""
        custom_names = [c["name"] for c in self.custom_categories]
        return BUILTIN_CATEGORIES + custom_names

    def ensure_category(self, name: str, category_type: str = "expense"):
        """
        Make sure a category exists -- if it's new, add it; if it already
        exists (built-in or custom), do nothing and just return its name.
        Never raises an error. Use this instead of add_category() whenever
        the category might already exist (e.g. user typing a category name
        in a simple add-transaction form).
        """
        name = name.strip()
        existing_names = [c.lower() for c in self.all_categories()]
        if name.lower() in existing_names:
            return name  # already exists, nothing to do

        return self.add_category(name, category_type=category_type)["name"]

    def add_category(self, name: str, category_type: str = "expense", icon: str = None, color: str = None, verbose: bool = False):
        """
        Add a new user-defined category.
        category_type: 'expense' or 'income' -- this directly answers your
        request: users can add a category under EITHER type, e.g. a custom
        income category like "Freelance Income" or a custom expense
        category like "Pet Care".
        """
        name = name.strip()
        if not name:
            raise ValueError("Category name cannot be empty")

        if category_type not in ("expense", "income"):
            raise ValueError("category_type must be 'expense' or 'income'")

        existing_names = [c.lower() for c in self.all_categories()]
        if name.lower() in existing_names:
            raise ValueError(f"Category '{name}' already exists")

        new_category = {
            "name": name,
            "type": category_type,
            "icon": icon or "tag",
            "color": color or "#6b7280",
            "created_at": datetime.now().isoformat(),
            "is_custom": True,
        }
        self.custom_categories.append(new_category)
        self._save_categories()
        if verbose:
            print(f"Added custom category: '{name}' ({category_type})")
        return new_category

    def remove_category(self, name: str, verbose: bool = False):
        """Remove a custom category. Built-in categories cannot be removed."""
        if name in BUILTIN_CATEGORIES:
            raise ValueError(f"'{name}' is a built-in category and cannot be removed")

        before = len(self.custom_categories)
        self.custom_categories = [c for c in self.custom_categories if c["name"] != name]
        if len(self.custom_categories) == before:
            raise ValueError(f"Custom category '{name}' not found")

        self._save_categories()
        # also clean up any rules pointing to the removed category
        self.user_rules = [r for r in self.user_rules if r["category"] != name]
        self._save_rules()
        if verbose:
            print(f"Removed custom category: '{name}'")

    def list_custom_categories(self):
        return self.custom_categories

    # -----------------------------------------------------------------
    # User rules: remembering manual corrections so the SAME merchant
    # doesn't need to be re-tagged every time it shows up again.
    # -----------------------------------------------------------------
    def add_rule(self, merchant: str = None, keyword: str = None, category: str = None, verbose: bool = False):
        """
        Remember that this merchant or keyword should always map to this
        category from now on. Call this whenever a user manually assigns
        or corrects a category on a transaction.

        At least one of merchant/keyword must be provided.
        """
        if not merchant and not keyword:
            raise ValueError("Must provide at least a merchant or a keyword")
        if not category:
            raise ValueError("Must provide a category")

        rule = {
            "merchant": merchant.strip().lower() if merchant else None,
            "keyword": keyword.strip().lower() if keyword else None,
            "category": category,
            "created_at": datetime.now().isoformat(),
        }

        # Replace existing rule for the same merchant/keyword if it exists,
        # rather than piling up duplicate/conflicting rules.
        self.user_rules = [
            r for r in self.user_rules
            if not (r["merchant"] == rule["merchant"] and r["keyword"] == rule["keyword"])
        ]
        self.user_rules.append(rule)
        self._save_rules()
        if verbose:
            print(f"Learned rule: merchant={merchant!r} keyword={keyword!r} -> {category}")
        return rule

    def match_rule(self, description: str, merchant: str = None):
        """
        Check if a user-defined rule matches this transaction.
        Returns the category name if matched, else None.
        Merchant match takes priority over keyword match (more specific).
        """
        merchant_lower = merchant.strip().lower() if merchant else ""
        description_lower = description.strip().lower() if description else ""

        # 1. Exact merchant match
        for rule in self.user_rules:
            if rule["merchant"] and merchant_lower and rule["merchant"] == merchant_lower:
                return rule["category"]

        # 2. Keyword match inside description
        for rule in self.user_rules:
            if rule["keyword"] and rule["keyword"] in description_lower:
                return rule["category"]

        return None

    def list_rules(self):
        return self.user_rules
