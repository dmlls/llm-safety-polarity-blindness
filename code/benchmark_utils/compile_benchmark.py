"""Compile the Forbidden Questions and MaliciousInstruct benchmark into a single one.

Links:
  * https://github.com/TrustAIRLab/JailbreakRadar/blob/main/forbidden_questions/forbidden_questions.csv
  * https://github.com/Princeton-SysML/Jailbreak_LLM/blob/main/data/MaliciousInstruct.txt

"""

import csv
import json
from pathlib import Path

from config import BENCHMARK_DIR


def compile_datasets(csv_path: Path, txt_path: Path, output_path: Path):
    combined_data = []
    global_id = 0

    # 1. Process ForbiddenQuestions (CSV)
    try:
        with open(csv_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                entry = {
                    "origin": "ForbiddenQuestions",
                    "global_id": global_id,
                    "type_id": row.get("type_id"),
                    "type": row.get("type"),
                    "question_id": row.get("question_id"),
                    "question": row.get("question", ""),
                }
                combined_data.append(entry)
                global_id += 1
    except FileNotFoundError:
        print(f"Error: {csv_path} not found.")

    # 2. Process MaliciousInstruct (TXT)
    try:
        with open(txt_path, mode="r", encoding="utf-8") as txt_file:
            for line in txt_file:
                clean_line = line.strip()
                if not clean_line:
                    continue  # Skip empty lines

                entry = {
                    "global_id": global_id,
                    "origin": "MaliciousInstruct",
                    "type_id": None,
                    "type": None,
                    "question_id": None,
                    "question": clean_line,
                }
                combined_data.append(entry)
                global_id += 1
    except FileNotFoundError:
        print(f"Error: {txt_path} not found.")

    # 3. Write to JSON
    with open(output_path, mode="w", encoding="utf-8") as json_file:
        json.dump(combined_data, json_file, indent=4, ensure_ascii=False)

    print(f"Successfully compiled {global_id} entries into {output_path}")


def main():
    compile_datasets(
        Path(BENCHMARK_DIR) / "source_datasets/forbidden_questions.csv",
        Path(BENCHMARK_DIR) / "source_datasets/MaliciousInstruct.txt",
        Path(BENCHMARK_DIR) / "en.json",
    )


if __name__ == "__main__":
    main()
