"""Calculate Quadratic Weighted Kappa between 2 raters."""

import json

from config import BENCHMARK_DIR
from sklearn.metrics import cohen_kappa_score

LABELS = [0, 1, 2]
RATINGS = ["en_annotated_00.json", "en_annotated_01.json"]


def calculate_agreement(file1_path, file2_path):
    with (
        open(file1_path, "r", encoding="utf-8") as f1,
        open(file2_path, "r", encoding="utf-8") as f2,
    ):
        data0 = json.load(f1)
        data1 = json.load(f2)

    # Extract the ratings using the key "harmfulness_rating"
    # This assumes the items in both files are in the same order
    rater0_scores = [item["harmfulness_rating"] for item in data0]
    rater1_scores = [item["harmfulness_rating"] for item in data1]

    # Check if the number of samples match
    if len(rater0_scores) != len(rater1_scores):
        raise ValueError("The number of ratings in the two files do not match.")

    # Calculate Quadratic Weighted Cohen's Kappa
    kappa = cohen_kappa_score(
        rater0_scores, rater1_scores, labels=LABELS, weights="quadratic"
    )

    return kappa


def main():
    file_1 = BENCHMARK_DIR / RATINGS[0]
    file_2 = BENCHMARK_DIR / RATINGS[1]

    kappa_value = calculate_agreement(file_1, file_2)
    print(f"\nWeighted Cohen's Kappa (Quadratic): {kappa_value:.4f}")

    if kappa_value > 0.8:
        print("Strength of Agreement: Almost Perfect")
    elif kappa_value > 0.6:
        print("Strength of Agreement: Substantial")
    elif kappa_value > 0.4:
        print("Strength of Agreement: Moderate")
    else:
        print("Strength of Agreement: Fair or Poor")
    print()


if __name__ == "__main__":
    assert len(RATINGS) == 2, "Specify only 2 rating files"
    main()
