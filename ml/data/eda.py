"""
Quick exploratory data analysis over dataset/issues.csv.
Run with: python ml/data/eda.py
Prints class distribution for category and priority so imbalance is visible
before training (informs use of macro-F1 rather than raw accuracy).
"""
import os
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "issues.csv")


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Total records: {len(df)}\n")

    print("Category distribution:")
    print(df["category"].value_counts())
    print()

    print("Priority distribution:")
    print(df["priority"].value_counts())
    print()

    print("Category x Priority cross-tab:")
    print(pd.crosstab(df["category"], df["priority"]))

    lengths = df["description"].str.len()
    print(f"\nDescription length — min: {lengths.min()}, max: {lengths.max()}, mean: {lengths.mean():.1f}")


if __name__ == "__main__":
    main()
