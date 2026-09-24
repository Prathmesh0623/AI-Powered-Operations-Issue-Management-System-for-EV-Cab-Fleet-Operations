# ML/NLP Documentation

## 1. Issue Category Classification

**Approach:** TF-IDF (unigrams+bigrams, max 5000 features) + Logistic
Regression, compared against Multinomial Naive Bayes and Linear SVM. The
model with the best macro-F1 on a held-out 20% test split is selected
automatically (`ml/training/train_category.py`).

**Why TF-IDF + Logistic Regression as the baseline?**
- Fast to train and to run inference with (no GPU, sub-second)
- Coefficients are inspectable — explainable to a non-ML stakeholder
- Performs well on short, templated support-ticket-style text without
  needing the data volume a deep learning approach would require
- Establishes a baseline other approaches can be measured against

**Result on the synthetic dataset:** ~100% accuracy / macro-F1 across all
three candidates. **This is not a meaningful benchmark of real-world
performance** — the synthetic generator (`ml/data/generate_dataset.py`)
builds each category from a distinct set of phrase templates, making the
classes trivially separable. On real, messier operator-written text, expect
meaningfully lower (and more informative) numbers. This is documented here
rather than left implicit, per the project's "don't fabricate results" rule.

## 2. Priority Prediction

**Approach:** TF-IDF text features combined with a one-hot encoded issue
category, fed into Logistic Regression and Random Forest; best macro-F1 is
kept (`ml/training/train_priority.py`).

**Result on the synthetic dataset:** ~27–30% accuracy, barely above the 25%
random baseline for 4 classes. **This is expected and intentional to
disclose:** in the dataset generator, priority is assigned via weighted
random sampling per category — there is no real signal in the text for a
model to learn. This mirrors the original design intent: priority in a real
system should depend heavily on structured operational context (is the
vehicle active, are backups available, is a driver's shift dependent on it),
which is exactly what the **Operational Impact Engine** (rule-based, not ML)
supplies instead. The text-based priority model remains in place as a
starting suggestion and as a demonstration of the full ML pipeline
(training → evaluation → comparison → serving), but it should not be
presented as reliable without richer, non-synthetic training data.

## 3. Duplicate/Similarity Detection

**Approach:** TF-IDF + cosine similarity, computed fresh at request time
against the current pool of open/assigned/in-progress issues (not a
persisted trained model — the "training data" is simply whatever issues
exist right now). Default similarity threshold: 0.30.

Never claims certainty — results are always labeled "potentially related",
and merging remains a manual decision by the operations manager.

**Verified behavior:** Two near-duplicate issue descriptions about the same
vehicle/symptom ("EV-105 battery temperature high" vs "EV-105 charging
problem... battery gets too hot") were correctly matched at 34.7% similarity
in an end-to-end test.

## 4. Operational Impact Engine

Deliberately **rule-based, not ML** (`services/impact_service.py`) — impact
reasoning needs to be transparent and auditable to an operations manager,
not a black box. Scoring factors (each adds points to a running total,
mapped to LOW/MEDIUM/HIGH/CRITICAL via configurable thresholds):

- Issue priority
- Whether the linked vehicle is currently active ("On Ride")
- Number of backup (Available) vehicles at the same hub
- Whether an on-shift driver depends on the linked vehicle
- Hub utilization (active vehicles vs. hub capacity)

Every result includes a human-readable "Potential impact is X because..."
explanation listing exactly which factors fired.

## Evaluation Methodology

For both classifiers: accuracy, macro-F1, weighted-F1, and a full
per-class classification report (precision/recall/F1) are printed during
training. Macro-F1 (not accuracy) is used for model selection because
issue categories/priorities are not uniformly distributed — accuracy alone
would reward a model that ignores minority classes.

## Model Serving

Both classifiers are trained offline and serialized with `joblib` to
`ml/models/*.pkl` and `ml/vectorizers/*.pkl`. `ml/inference/*_predictor.py`
loads them once at import time (module-level singletons) — never reloaded
per-request, per the project's performance requirements. If a model file is
missing (not yet trained), inference functions degrade gracefully — `is_ready()`
returns `False` and dependent API endpoints respond `503` rather than crashing.

## Retraining

```bash
python ml/data/generate_dataset.py   # optional: fresh synthetic data
python ml/training/train_category.py
python ml/training/train_priority.py
```
