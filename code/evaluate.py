"""Evaluate LLM outputs, classifying the level of harm."""

import argparse
import threading
from pathlib import Path

from dotenv import load_dotenv

from evaluation import Evaluator
from utils import load_config


def collect_output_paths(output_path: str) -> list[Path]:
    evaluation_path = Path(output_path)
    output_paths: list[Path] = set(
        path.parent for path in evaluation_path.glob("**/*") if path.is_file()
    )
    return output_paths


def main(args):
    config = load_config()

    dataset_path = config.get("dataset_path")
    judge_models: list[str] = config.get("judge_models")
    output_path: str = args.output_path or config.get("output_path")
    evaluation_path: str = args.evaluation_path or config.get("evaluation_path")

    output_paths = collect_output_paths(output_path)

    total_runs: int = len(output_paths)
    max_parallel_runs: int = config.get("max_parallel_runs") or total_runs

    threads = []
    for i, path in enumerate(output_paths):
        for j, judge_model in enumerate(judge_models):
            e = Evaluator(judge_model, dataset_path, path, evaluation_path)
            idx = -5 if "openrouter" in str(path) else -4
            t = threading.Thread(
                target=e.evaluate,
                kwargs={
                    "tqdm_desc": " | ".join(
                        [p for p in path.resolve().parts if p != "/"][idx:]
                    ),
                    "tqdm_position": i + j,
                },
            )
            threads.append(t)
            if len(threads) == max_parallel_runs:
                # Start each thread
                for t in threads:
                    t.start()
                # Wait for all threads to finish before continuing.
                for t in threads:
                    t.join()
                threads = []

    # Run remaining threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    threads = []


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run LLM inference")
    parser.add_argument(
        "--judge-models",
        nargs="+",
        type=str,
        default=None,
        help="The judge models to evaluate outputs with",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Base path where the LLM outputs to evaluate are",
    )
    parser.add_argument(
        "--evaluation-path",
        type=str,
        default=None,
        help="The path where to output the evaluation results",
    )

    main(parser.parse_args())
