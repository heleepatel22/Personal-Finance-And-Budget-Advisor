HOW TO RUN THIS
=================

FOLDER CONTENTS (only what's actually needed):
  add_transaction.py                      - <<< RUN THIS
  category_manager.py                     - handles custom categories + learned merchant rules
  ml/category_classifier.py               - the ML model code (training + prediction)
  trained_models/category_classifier.pkl  - the already-trained model
  expense_training_dataset_clean.csv      - training data (only needed if you retrain)

STEPS:
  1. Open this folder in VS Code
  2. Open a terminal (Terminal -> New Terminal)
  3. Install requirements (only once):
       pip install pandas scikit-learn joblib
  4. Run:
       python add_transaction.py

WHAT IT DOES:
  4 prompts -- Description, Merchant, Amount, Category -- then saves and
  prints "Data added, thank you." No menus, no confidence scores, no errors.

  - Category already exists (built-in or one you added before) -> just used.
  - Category left blank -> it checks if this merchant was taught before;
    if yes, uses that. If not, the ML model predicts it and shows you the
    predicted category before the thank-you message.
  - Category is brand new -> created automatically, no announcement.

  Every transaction is appended to transactions_dataset.csv (created the
  first time you run it) -- this file grows over time and can be fed back
  into ml/category_classifier.py to retrain the model on real usage later.

PRIORITY ORDER (when category is left blank):
  1. Learned rule (a merchant you've corrected/taught before) -- wins
  2. ML model prediction

RETRAINING FROM SCRATCH (optional):
  python ml/category_classifier.py
  (regenerates trained_models/category_classifier.pkl from
  expense_training_dataset_clean.csv)
