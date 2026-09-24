"""
Trains the priority-prediction model using text features (TF-IDF) combined
with the issue category as a structured one-hot feature, since priority
depends on both what was said and what kind of issue it is.

Compares Logistic Regression and Random Forest; keeps whichever wins on
macro-F1 (priority classes are imbalanced, so accuracy alone is misleading).

Run with: python ml/training/train_priority.py
Outputs: ml/models/priority_model.pkl, ml/vectorizers/priority_vectorizer.pkl,
         ml/models/priority_category_encoder.pkl
"""
import os
import sys
import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.preprocessing.text_preprocessing import combine_title_description

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "issues.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
VECTORIZER_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorizers")


def main():
    df = pd.read_csv(DATA_PATH)
    df["text"] = df.apply(lambda r: combine_title_description(r["title"], r["description"]), axis=1)

    X_train_df, X_test_df, y_train, y_test = train_test_split(
        df[["text", "category"]], df["priority"], test_size=0.2, random_state=42, stratify=df["priority"]
    )

    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), min_df=2)
    X_train_text = vectorizer.fit_transform(X_train_df["text"])
    X_test_text = vectorizer.transform(X_test_df["text"])

    encoder = OneHotEncoder(handle_unknown="ignore")
    X_train_cat = encoder.fit_transform(X_train_df[["category"]])
    X_test_cat = encoder.transform(X_test_df[["category"]])

    X_train = hstack([X_train_text, X_train_cat])
    X_test = hstack([X_test_text, X_test_cat])

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        macro_f1 = f1_score(y_test, preds, average="macro")
        results[name] = {"model": model, "accuracy": acc, "macro_f1": macro_f1}
        print(f"\n=== {name} ===")
        print(f"Accuracy: {acc:.4f}  |  Macro F1: {macro_f1:.4f}")
        print(classification_report(y_test, preds, zero_division=0))

    best_name = max(results, key=lambda k: results[k]["macro_f1"])
    best_model = results[best_name]["model"]
    print(f"\nSelected model: {best_name} (macro F1 = {results[best_name]['macro_f1']:.4f})")

    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(VECTORIZER_DIR, exist_ok=True)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "priority_model.pkl"))
    joblib.dump(vectorizer, os.path.join(VECTORIZER_DIR, "priority_vectorizer.pkl"))
    joblib.dump(encoder, os.path.join(MODEL_DIR, "priority_category_encoder.pkl"))
    joblib.dump(best_name, os.path.join(MODEL_DIR, "priority_model_name.pkl"))
    print("Model, vectorizer, and category encoder saved.")


if __name__ == "__main__":
    main()
