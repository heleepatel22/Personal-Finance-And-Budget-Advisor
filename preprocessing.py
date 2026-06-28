"""
preprocessing.py
-----------------
Cleans raw transaction data before it reaches feature engineering or training.
Mirrors the requirements in 07_AI_ML_Modules.docx, section 3.1.

Run this BEFORE training the category classifier, expense predictor,
or anomaly detector.
"""

import pandas as pd
import re


def normalize_description(text: str) -> str:
    """Lowercase, strip whitespace/punctuation noise for the category classifier."""
    if pd.isna(text):
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)          # collapse multiple spaces
    text = re.sub(r"[^a-z0-9\s\-#]", "", text)  # drop stray punctuation like !!
    return text.strip()


def drop_duplicate_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop duplicate transactions: same date, amount, description within
    a short window. Here we treat exact (date, amount, description) matches
    as duplicates -- adjust to a date-range window if your real data needs it.
    """
    before = len(df)
    df = df.drop_duplicates(subset=["date", "amount", "description"], keep="first")
    after = len(df)
    print(f"Dropped {before - after} duplicate rows")
    return df


def handle_missing_categories(df: pd.DataFrame):
    """
    Per spec: missing categories are NOT dropped or imputed --
    they're left null and routed to the prediction pipeline instead.
    Returns (labeled_df, unlabeled_df).
    """
    labeled = df[df["category"].notna() & (df["category"] != "")].copy()
    unlabeled = df[df["category"].isna() | (df["category"] == "")].copy()
    print(f"{len(labeled)} labeled rows (training set)")
    print(f"{len(unlabeled)} unlabeled rows (set aside for prediction, not training)")
    return labeled, unlabeled


def clean_merchant(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing merchant with a placeholder rather than dropping the row --
    description alone is still usable by the classifier."""
    df["merchant"] = df["merchant"].fillna("Unknown").replace("", "Unknown")
    return df


def validate_amounts(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with non-positive amounts -- shouldn't exist, but defensive."""
    before = len(df)
    df = df[df["amount"] > 0]
    after = len(df)
    if before != after:
        print(f"Dropped {before - after} rows with invalid (<=0) amounts")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure date column is real datetime, drop unparseable rows."""
    before = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    after = len(df)
    if before != after:
        print(f"Dropped {before - after} rows with unparseable dates")
    return df


def preprocess(input_path: str, labeled_out: str, unlabeled_out: str):
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} raw rows")

    df = parse_dates(df)
    df = validate_amounts(df)
    df = drop_duplicate_transactions(df)
    df = clean_merchant(df)
    df["description_clean"] = df["description"].apply(normalize_description)

    # NOTE: currency conversion step from the spec (currency/converter.py)
    # is skipped here since this synthetic dataset is single-currency (INR).
    # In the real app, convert df['amount'] to the user's base currency here.

    labeled, unlabeled = handle_missing_categories(df)

    labeled.to_csv(labeled_out, index=False)
    unlabeled.to_csv(unlabeled_out, index=False)
    print(f"\nSaved cleaned training set -> {labeled_out}")
    print(f"Saved unlabeled set (for prediction) -> {unlabeled_out}")


if __name__ == "__main__":
    preprocess(
        input_path="expense_training_dataset.csv",
        labeled_out="expense_training_dataset_clean.csv",
        unlabeled_out="expense_unlabeled_for_prediction.csv",
    )
