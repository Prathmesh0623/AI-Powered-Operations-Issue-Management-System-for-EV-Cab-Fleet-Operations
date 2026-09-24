"""
Loads the trained priority model once at import time. See train_priority.py's
docstring and the ML documentation for an honest note on this model's current
accuracy ceiling given the synthetic training data.
"""
import os
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from ml.preprocessing.text_preprocessing import combine_title_description

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "priority_model.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "..", "vectorizers", "priority_vectorizer.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "priority_category_encoder.pkl")

_model = None
_vectorizer = None
_encoder = None

try:
    _model = joblib.load(MODEL_PATH)
    _vectorizer = joblib.load(VECTORIZER_PATH)
    _encoder = joblib.load(ENCODER_PATH)
except Exception:
    pass


def is_ready() -> bool:
    return _model is not None and _vectorizer is not None and _encoder is not None


def predict_priority(title: str, description: str, category: str = "Other"):
    if not is_ready():
        return None, None

    text = combine_title_description(title, description)
    if not text:
        return None, None

    text_vec = _vectorizer.transform([text])
    cat_vec = _encoder.transform(pd.DataFrame([[category]], columns=["category"]))
    combined = hstack([text_vec, cat_vec])

    if hasattr(_model, "predict_proba"):
        probs = _model.predict_proba(combined)[0]
        idx = int(np.argmax(probs))
        return _model.classes_[idx], round(float(probs[idx]), 4)

    prediction = _model.predict(combined)[0]
    return prediction, None
