"""LLM inference."""

import argparse
import threading

from dotenv import load_dotenv

from pipelines import (
    PREPROCESS_PIPELINES,
    AntonymPipeline,
    AsIsPipeline,
    NegationPipeline,
    Preprocessor,
    SynonymPipeline,
)
from utils import load_config


def run_threads(threads):
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    threads.clear()


def main(args):
    config = load_config()

    pipelines: list[list[str]] = config.get("pipelines")
    models: list[str] = args.models or config.get("models")
    preprocessing_model: str = args.preprocessing_model or config.get(
        "preprocessing_model"
    )
    languages: list[str] = args.languages or config.get("languages")
    dataset_path: str = args.dataset_path or config.get("dataset_path")
    output_path: str = args.output_path or config.get("output_path")

    total_runs: int = len(pipelines) * len(models) * len(languages)
    max_parallel_runs: int = min(
        config.get("max_parallel_runs") or total_runs, total_runs
    )

    threads = []
    tqdm_position = 0
    for pipeline in PREPROCESS_PIPELINES:
        for language in languages:
            t = threading.Thread(
                target=Preprocessor.process_dataset,
                kwargs={
                    "language": language,
                    "model": preprocessing_model,
                    "pipeline": pipeline,
                    "dataset_path": dataset_path,
                    "file_suffix": pipeline,
                    "desc": f"Preprocess {pipeline} ({language})",
                    "tqdm_position": tqdm_position,
                },
            )
            threads.append(t)
            tqdm_position += 1
            if len(threads) == max_parallel_runs and pipeline != "annotated":
                run_threads(threads)
        if pipeline == "annotated":
            run_threads(threads)

    # Run remaining threads
    run_threads(threads)

    # Local models:
    # for model in models:
    #     for language in languages:
    #         for pipeline_chain in pipelines:

    for pipeline_chain in pipelines:
        for language in languages:
            for model in models:
                pipeline = None
                if "as_is" in pipeline_chain:
                    pipeline = AsIsPipeline
                elif "negation" in pipeline_chain:
                    pipeline = NegationPipeline
                elif "antonyms" in pipeline_chain:
                    pipeline = AntonymPipeline
                elif "synonyms" in pipeline_chain:
                    pipeline = SynonymPipeline
                if pipeline:
                    p = pipeline(model, language, dataset_path, output_path)
                    t = threading.Thread(
                        target=p.run,
                        kwargs={
                            "with_wrapper": "wrapper" in pipeline_chain,
                            "tqdm_position": len(threads),
                        },
                    )
                    threads.append(t)
                if len(threads) == max_parallel_runs:
                    run_threads(threads)

    # Run remaining threads
    run_threads(threads)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run LLM inference")
    parser.add_argument(
        "--models",
        nargs="+",
        type=str,
        default=None,
        help="The models to run inference for",
    )
    parser.add_argument(
        "--preprocessing-model",
        type=str,
        default=None,
        help="The model to preprocess the prompts with (e.g., to negate them)",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        type=str,
        default=None,
        help="The languages to run inference for",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=None,
        help="The path to the dataset to run the inference with",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Base path to save the LLM inference output",
    )

    main(parser.parse_args())
