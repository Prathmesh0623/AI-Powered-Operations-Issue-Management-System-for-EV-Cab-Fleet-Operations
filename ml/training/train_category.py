"""
Trains the issue-category classifier.

Baseline: TF-IDF + Logistic Regression, chosen because it is fast, explainable,
and performs well on short, templated support-ticket-style text without the
data volume deep learning would need. Naive Bayes and Linear SVM are trained
alongside as points of comparison; the model with the best macro-F1 on the
held-out test split is the one actually saved and served.

Run with: python ml/training/train_category.py
Outputs: ml/models/category_model.pkl, ml/vectorizers/category_vectorizer.pkl
"""
import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score, classification_report

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.preprocessing.text_preprocessing import combine_title_description

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "issues.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
VECTORIZER_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorizers")


def main():
    df = pd.read_csv(DATA_PATH)
    df["text"] = df.apply(lambda r: combine_title_description(r["title"], r["description"]), axis=1)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["category"], test_size=0.2, random_state=42, stratify=df["category"]
    )

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "MultinomialNB": MultinomialNB(),
        "LinearSVC": LinearSVC(class_weight="balanced"),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train_vec, y_train)
        preds = model.predict(X_test_vec)
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
    joblib.dump(best_model, os.path.join(MODEL_DIR, "category_model.pkl"))
    joblib.dump(vectorizer, os.path.join(VECTORIZER_DIR, "category_vectorizer.pkl"))
    joblib.dump(best_name, os.path.join(MODEL_DIR, "category_model_name.pkl"))
    print("Model and vectorizer saved.")


if __name__ == "__main__":
    main()
