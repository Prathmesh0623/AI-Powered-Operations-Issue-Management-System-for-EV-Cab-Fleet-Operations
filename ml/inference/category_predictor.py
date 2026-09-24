"""
Loads the trained category model once at import time and exposes a single
predict_category() function. Never reload the model per-request.
"""
import os
import joblib
from ml.preprocessing.text_preprocessing import combine_title_description

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "category_model.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "..", "vectorizers", "category_vectorizer.pkl")

_model = None
_vectorizer = None
_load_error = None

try:
    _model = joblib.load(MODEL_PATH)
    _vectorizer = joblib.load(VECTORIZER_PATH)
except Exception as e:  # model not trained yet — degrade gracefully
    _load_error = str(e)


def is_ready() -> bool:
    return _model is not None and _vectorizer is not None


def predict_category(title: str, description: str):
    """Returns (predicted_category: str | None, confidence: float | None)."""
    if not is_ready():
        return None, None

    text = combine_title_description(title, description)
    if not text:
        return None, None

    vec = _vectorizer.transform([text])

    if hasattr(_model, "predict_proba"):
        probs = _model.predict_proba(vec)[0]
        idx = probs.argmax()
        return _model.classes_[idx], round(float(probs[idx]), 4)

    # LinearSVC has no predict_proba; use decision_function margin as a confidence proxy.
    prediction = _model.predict(vec)[0]
    if hasattr(_model, "decision_function"):
        import numpy as np
        scores = _model.decision_function(vec)[0]
        margin = float(np.max(scores) - np.sort(scores)[-2]) if len(scores) > 1 else 1.0
        confidence = round(min(1.0, 0.5 + margin / 4), 4)
    else:
        confidence = None
    return prediction, confidence
