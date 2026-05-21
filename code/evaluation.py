"""Evaluator."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

from tqdm import tqdm

from prompts import Prompt
from utils import inference, parse_json


class Evaluator:

    def __init__(
        self,
        judge_model: str,
        dataset_path: str,
        output_path: str,
        evaluation_path: str,
    ):
        self.judge_model: str = judge_model
        self.dataset_path: Path = Path(dataset_path)
        self.output_path: Path = Path(output_path)
        self.evaluation_path: Path = Path(evaluation_path)
        self.stats_filename = "_stats.json"

    def _evaluate_single(self, dataset, input_file, eval_file):
        with open(input_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                with open(
                    self.evaluation_path / "errors_input.txt", "a", encoding="utf-8"
                ) as f:
                    f.write(f"Could not load JSON:\n{input_file}\n\n\n")
                return

        idx = data["id"]
        conversation = data["conversation"]

        # Remove the system message from the conversation if it exists
        if conversation[0]["role"] == "system":
            conversation = conversation[1:]
        try:
            conversation = {
                "prompt": dataset[idx],
                "response": (
                    conversation[1]["content"]["choices"][0]["message"]["content"]
                    if not isinstance(conversation[1]["content"], str)
                    else conversation[1]["content"]
                ),
            }
            if None in (conversation["prompt"], conversation["response"]):
                raise TypeError("Prompt or response is None")
        except TypeError:
            with open(
                self.evaluation_path / "errors_input.txt", "a", encoding="utf-8"
            ) as f:
                f.write(
                    "Could not parse"
                    f" {input_file}:\n{json.dumps(conversation, indent=4, ensure_ascii=False)}\n\n\n"
                )
            return

        eval_messages = [
            {"role": "system", "content": Prompt.JUDGE},
            {
                "role": "user",
                "content": json.dumps(conversation, indent=2, ensure_ascii=False),
            },
        ]

        eval_response = inference(self.judge_model, eval_messages)

        try:
            eval_result = parse_json(eval_response)
        except ValueError:
            with open(
                self.evaluation_path / "errors_output.txt", "a", encoding="utf-8"
            ) as f:
                f.write(f"Could not eval for {input_file}:\n{eval_response}\n\n\n")
            return
        # Merge evaluation into the output JSON.
        data["evaluation"] = eval_result

        with open(eval_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def evaluate(self, **kwargs):
        tqdm_desc = kwargs.get("tqdm_desc")
        tqdm_position = kwargs.get("tqdm_position")
        # Input/output paths
        self.evaluation_path.mkdir(parents=True, exist_ok=True)

        eval_dir: Path = None

        # Iterate over all JSON files
        for input_file in tqdm(
            self.output_path.iterdir(), desc=tqdm_desc, position=tqdm_position
        ):
            if not input_file.is_file() or input_file.suffix != ".json":
                continue
            language = "en"
            parts = input_file.parts
            if any(p == "es" for p in parts):
                language = "es"
            elif any(p == "cs" for p in parts):
                language = "cs"
            with open(
                self.dataset_path / f"{language}_annotated.json", "r", encoding="utf-8"
            ) as f:
                dataset = json.load(f)
            dataset = {
                sample["global_id"]: (
                    sample.get("question_corrected", None) or sample["question"]
                )
                for sample in dataset
            }
            idx = -6 if "openrouter" in str(input_file) else -5
            eval_file = self.evaluation_path / "/".join(parts[idx:])
            if eval_dir is None:
                eval_dir = eval_file.parent
            if eval_file.exists():
                # print(f"Output already evaluated: {eval_file}. Skipping.")
                continue
            if not eval_file.parent.exists():
                eval_file.parent.mkdir(parents=True, exist_ok=True)

            self._evaluate_single(dataset, input_file, eval_file)

        self._write_stats(eval_dir)

    def _write_stats(self, eval_dir: Path):
        stats_file = eval_dir / self.stats_filename

        # if stats_file.exists():
        #     print(f"Statistics already calculated: {stats_file}")
        #     return

        # Initialize stats containers
        stats_entries = {
            "total_entries": 0,
            "harm_0": 0,
            "harm_1": 0,
            "harm_2": 0,
            "harm_3": 0,
            "harm_4": 0,
            "harm_5": 0,
            "disclaimer": 0,
            "refusal": 0,
        }

        stats = {}
        stats["_all"] = defaultdict(lambda: stats_entries.copy())
        for file in eval_dir.iterdir():
            if (
                not file.is_file()
                or file.suffix != ".json"
                or file.name == self.stats_filename
            ):
                continue

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            origin = data.get("origin", "unknown")

            if origin not in stats:
                stats[origin] = defaultdict(lambda: stats_entries.copy())

            type_ = data.get("type", "unknown")
            eval_data = data.get("evaluation", {})
            try:
                harm_level = int(eval_data.get("harm", 0))
            except (AttributeError, ValueError):
                with open(
                    self.evaluation_path / "errors_input.txt", "a", encoding="utf-8"
                ) as f:
                    f.write(f"Could not get evaluation {file}\n")
                continue
            disclaimer = eval_data.get("disclaimer", False)
            refusal = eval_data.get("refusal", False)

            # Update global and label-specific stats
            for orig in ["_all", origin]:
                for typ in [type_, "_all"]:
                    stats[orig][typ]["total_entries"] += 1
                    stats[orig][typ][f"harm_{harm_level}"] += 1
                    if disclaimer:
                        stats[orig][typ]["disclaimer"] += 1
                    if refusal:
                        stats[orig][typ]["refusal"] += 1

        # Finalize stats with percentages.
        output_stats = {}
        for origin, origin_stats in stats.items():
            for type_, values in origin_stats.items():
                type_ = str(type_)
                total = values["total_entries"]
                harm_values = []
                for harm_level in range(6):
                    harm_values += [harm_level] * values[f"harm_{harm_level}"]
                mean_harm = mean(harm_values)
                std_harm = pstdev(harm_values)
                disclaimer_rate = (values["disclaimer"] / total * 100) if total else 0.0
                refusal_rate = (values["refusal"] / total * 100) if total else 0.0

                if origin not in output_stats:
                    output_stats[origin] = {}
                output_stats[origin][type_] = values | {
                    "mean_harm": round(mean_harm, 2),
                    "std_harm": round(std_harm, 2),
                    "disclaimer_rate": round(disclaimer_rate, 2),
                    "refusal_rate": round(refusal_rate, 2),
                }

        # print(output_stats)
        # Sort output stats so "_all" appears first (alphabetically sorted)
        for origin, values in output_stats.items():
            output_stats_sorted = {k: values[k] for k in sorted(values)}
            output_stats[origin] = output_stats_sorted

        # Write to file
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(output_stats, f, indent=4, ensure_ascii=False)

        # print(f"Stats written to: {stats_file}")
        # print(output_stats["_all"]["_all"])
