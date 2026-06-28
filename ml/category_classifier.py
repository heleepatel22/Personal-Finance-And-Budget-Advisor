"""
category_classifier.py
------------------------
Trains and serves the 'Automatic Categorization' model (Module 4 of the spec).

Per 07_AI_ML_Modules.docx:
  - Pipeline: TfidfVectorizer(max_features=500) -> MultinomialNB()
  - Input features: transaction description (+ optionally merchant, amount)
  - Target: category name
  - Falls back to rule-based categorization if confidence < threshold (0.55)
  - Saved as trained_models/category_classifier.pkl via joblib

This script is split into two parts:
  1. train_category_classifier()  -> trains, evaluates, saves the model
  2. CategoryPredictor             -> loads the saved model and predicts on new data

Run directly:
    python category_classifier.py

Then use CategoryPredictor in your Flask app (ml/predictor.py) like:
    from ml.category_classifier import CategoryPredictor
    predictor = CategoryPredictor("trained_models/category_classifier.pkl")
    category, confidence = predictor.predict("Swiggy order #1234", merchant="Swiggy", amount=450)
"""

import os
import re
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# ---------------------------------------------------------------------------
# Config — edit these paths/values to match your real project structure
# ---------------------------------------------------------------------------
DATA_PATH = "expense_training_dataset_clean.csv"   # output of preprocessing.py
MODEL_OUT_PATH = "trained_models/category_classifier.pkl"
TEXT_COLUMN = "description_clean"   # produced by preprocessing.py
MERCHANT_COLUMN = "merchant"
LABEL_COLUMN = "category"
CONFIDENCE_THRESHOLD = 0.55          # below this -> fall back to rule-based categorizer
MAX_TFIDF_FEATURES = 500
RANDOM_STATE = 42


def normalize_text(text: str) -> str:
    """Same normalization used in preprocessing.py -- kept here too so this
    file can run standalone on raw, uncleaned text at prediction time."""
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s\-#]", "", text)
    return text.strip()


def build_input_text(description: str, merchant: str = None) -> str:
    """
    Combines description + merchant into a single text field for TF-IDF.
    Merchant is a strong signal (e.g. 'Swiggy' almost always = Food), so we
    concatenate it rather than using description alone.
    """
    desc = normalize_text(description)
    merch = normalize_text(merchant) if merchant else ""
    if merch and merch != "unknown":
        return f"{desc} {merch}"
    return desc


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_category_classifier(
    data_path: str = DATA_PATH,
    model_out_path: str = MODEL_OUT_PATH,
    test_size: float = 0.2,
):
    print(f"Loading training data from {data_path} ...")
    df = pd.read_csv(data_path)

    # Drop any rows that somehow still have no label (defensive — preprocessing
    # should have already routed these to the unlabeled set)
    df = df[df[LABEL_COLUMN].notna() & (df[LABEL_COLUMN] != "")].copy()
    print(f"Training on {len(df)} labeled rows across {df[LABEL_COLUMN].nunique()} categories")

    # Build combined text input (description + merchant)
    df["input_text"] = df.apply(
        lambda row: build_input_text(row.get(TEXT_COLUMN, row.get("description")), row.get(MERCHANT_COLUMN)),
        axis=1,
    )

    X = df["input_text"]
    y = df[LABEL_COLUMN]

    # Guard against categories with too few samples to stratify
    label_counts = y.value_counts()
    rare_labels = label_counts[label_counts < 2].index.tolist()
    if rare_labels:
        print(f"Warning: dropping categories with <2 samples (can't split): {rare_labels}")
        mask = ~y.isin(rare_labels)
        X, y = X[mask], y[mask]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y
    )

    print("Building pipeline: TF-IDF -> Multinomial Naive Bayes")
    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=MAX_TFIDF_FEATURES, ngram_range=(1, 2))),
        ("clf", MultinomialNB()),
    ])

    model.fit(X_train, y_train)

    # --- Evaluation ---
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print(f"ACCURACY: {accuracy:.4f}  ({accuracy*100:.2f}%)")
    print("=" * 60)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    print("Confusion Matrix (rows=actual, cols=predicted):")
    labels_sorted = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels_sorted)
    cm_df = pd.DataFrame(cm, index=labels_sorted, columns=labels_sorted)
    print(cm_df)

    # --- Save model ---
    os.makedirs(os.path.dirname(model_out_path), exist_ok=True)
    joblib.dump(model, model_out_path)
    print(f"\nModel saved -> {model_out_path}")

    return model, accuracy


# ---------------------------------------------------------------------------
# Prediction (this is what ml/predictor.py imports and calls in the Flask app)
# ---------------------------------------------------------------------------
class CategoryPredictor:
    """
    Loads the saved category_classifier.pkl and predicts categories for new
    transactions. Falls back to None (signal to use rule-based categorizer
    in transactions/categorizer.py) when confidence is below threshold.
    """

    def __init__(self, model_path: str = MODEL_OUT_PATH, confidence_threshold: float = CONFIDENCE_THRESHOLD):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"No trained model found at {model_path}. Run train_category_classifier() first."
            )
        self.model = joblib.load(model_path)
        self.confidence_threshold = confidence_threshold
        self.classes_ = self.model.named_steps["clf"].classes_

    def predict(self, description: str, merchant: str = None, amount: float = None):
        """
        Returns (category_name, confidence) if confidence >= threshold,
        otherwise (None, confidence) -- the None signals the caller to fall
        back to transactions/categorizer.py's rule-based logic.

        `amount` is accepted for interface compatibility with predictor.py's
        predict_category(description, amount, merchant) signature, but is
        not currently used by this Naive Bayes text model. Extend here if
        you want to add amount as a numeric feature later (e.g. via a
        ColumnTransformer combining TF-IDF text + scaled numeric amount).
        """
        input_text = build_input_text(description, merchant)
        if not input_text:
            return None, 0.0

        probabilities = self.model.predict_proba([input_text])[0]
        best_idx = np.argmax(probabilities)
        best_category = self.classes_[best_idx]
        confidence = float(probabilities[best_idx])

        if confidence < self.confidence_threshold:
            return None, confidence

        return best_category, confidence

    def predict_batch(self, df: pd.DataFrame, description_col="description", merchant_col="merchant"):
        """Predict categories for an entire DataFrame at once (e.g. after CSV import)."""
        results = []
        for _, row in df.iterrows():
            category, confidence = self.predict(
                row.get(description_col), row.get(merchant_col)
            )
            results.append({"category": category, "confidence": confidence})
        return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Run as a script: trains the model and demonstrates predictions on the
# unlabeled set produced by preprocessing.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    model, accuracy = train_category_classifier()

    unlabeled_path = "expense_unlabeled_for_prediction.csv"
    if os.path.exists(unlabeled_path):
        print("\n" + "=" * 60)
        print("DEMO: predicting categories for previously unlabeled transactions")
        print("=" * 60)

        predictor = CategoryPredictor(MODEL_OUT_PATH)
        unlabeled_df = pd.read_csv(unlabeled_path)

        sample = unlabeled_df.head(10)
        for _, row in sample.iterrows():
            category, confidence = predictor.predict(row["description"], row.get("merchant"))
            fallback_note = "  <- low confidence, use rule-based fallback" if category is None else ""
            print(f"  '{row['description'][:45]:45s}' -> {category}  (confidence: {confidence:.2f}){fallback_note}")
