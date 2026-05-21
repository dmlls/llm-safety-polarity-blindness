"""Tools to negate a given dataset."""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from prompts import NEGATE_PROMPT
from utils import inference, populate_prompt_template


def negate_prompt(model, prompt, lang) -> str:
    prompt = populate_prompt_template(NEGATE_PROMPT[lang], prompt)
    conversation = [{"role": "user", "content": prompt}]
    negated_prompt = inference(model, conversation)
    return negated_prompt if negated_prompt is not None else ""


def main(args):
    load_dotenv()
    with open(
        Path(args.dataset_base_path) / args.dataset_name / f"{args.lang}.json",
        "r",
        encoding="utf-8",
    ) as f:
        dataset = json.load(f)

    for sample in tqdm(dataset):
        sample["input"] = negate_prompt(args.model, sample["input"], args.lang)
        # We save at every iteration (inefficient but we don't lose data :)
        with open(
            Path(args.dataset_base_path)
            / args.dataset_name
            / f"{args.lang}_negated.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(dataset, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Negate the prompts of a given dataset."
    )
    parser.add_argument(
        "--output-base-path",
        type=str,
        default="datasets",
        help="Base path to save the negated prompts.",
    )
    parser.add_argument(
        "--dataset-base-path",
        type=str,
        default="datasets",
        help="Base path to the dataset folder.",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="AttaQ_sample1",
        help="Name of the dataset to negate.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5-nano-2025-08-07",
        help="Model to use to generate the negations.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="en",
        help="Language code of the dataset.",
    )
    main(parser.parse_args())
