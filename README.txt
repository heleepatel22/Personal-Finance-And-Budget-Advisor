HOW TO RUN THIS DEMO
======================

This is a small, standalone test project to check whether the trained
category classifier model gives correct predictions, AND to test the
new custom-category feature (users can add their own categories and
correct wrong predictions). No Flask, no database -- just the model,
JSON file storage, and test scripts.

FOLDER CONTENTS:
  ml/category_classifier.py          - training code + CategoryPredictor class
  trained_models/category_classifier.pkl  - the already-trained model
  expense_training_dataset_clean.csv - cleaned training data (used if you retrain)
  expense_unlabeled_for_prediction.csv - sample rows with no category (used for testing)
  preprocessing.py                   - data cleaning script (only needed if you regenerate data)

  category_manager.py                 - handles custom categories + user rules (JSON storage)
  categorizer.py                      - combines user rules + ML model + keyword fallback
  add_transaction.py                  - <<< RUN THIS for the simplest flow: just type
                                          description, merchant, amount, category -> saved.
  test_prediction.py                  - tests the RAW ML model only (no custom categories)
  interactive_categorizer.py          - menu-driven tool to test predictions + corrections

STEPS:
  1. Open this folder in VS Code
  2. Open a terminal (Terminal -> New Terminal)
  3. Install requirements:
       pip install pandas scikit-learn joblib
  4. Run the simple version:
       python add_transaction.py

WHAT add_transaction.py DOES:
  4 prompts -- description, merchant, amount, category -- then saves and
  prints "Data added, thank you." No menus, no confidence scores, no
  errors, no extra noise.

  - If you type a category that already exists (built-in or custom) ->
    it's just used, no error.
  - If you leave category BLANK -> the ML model predicts it for you, and
    the predicted category name is shown before the thank-you message.
  - If you type a brand new category -> it's silently created, no
    announcement.
  - Every transaction (yours or predicted) is appended to
    transactions_dataset.csv -- this file grows over time and can be
    used to retrain the model later so it keeps learning from real usage.

WHAT THE INTERACTIVE TOOL LETS YOU DO:
  1. Categorize any transaction (typed by you) and see the prediction
  2. Add your own custom category (e.g. "Pet Care", "Freelance Income")
     -- choose expense or income type
  3. Correct a wrong prediction -- this teaches the system to remember
     that merchant/description for next time
  4. List every category (12 built-in + any custom ones you added)
  5. List every rule you've taught the system so far

HOW THE PRIORITY ORDER WORKS (categorizer.py):
  1. User-defined rule (a merchant/keyword you've manually corrected before) -- WINS
  2. ML model prediction (if confidence >= 55%)
  3. Simple keyword fallback (covers the 12 built-in categories only)
  4. "Uncategorized" (last resort)

  This means: once you correct a transaction ONCE, the system never asks
  the ML model again for that same merchant -- your correction is final.

DATA STORAGE (for this demo -- swap for real DB tables in your Flask app):
  custom_categories.json    - created automatically when you add a category
  user_category_rules.json - created automatically when you correct a prediction

  These files are created fresh the first time you add a category or
  correction, and persist between runs of the script.

IF YOU WANT TO RETRAIN THE ML MODEL FROM SCRATCH:
  python ml/category_classifier.py
  (this regenerates trained_models/category_classifier.pkl -- only retrains
  on the 12 built-in categories; custom categories are handled separately
  and don't require retraining)

IF YOU JUST WANT TO TEST THE RAW ML MODEL (no custom category logic):
  python test_prediction.py

