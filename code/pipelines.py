"""Pipelines for polarity blindness safety in LLMs."""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path

import litellm
from litellm import APIError, BadRequestError
from tqdm import tqdm

from prompts import Prompt, populate_prompt_template
from utils import completion_without_reasoning, inference

PREPROCESS_PIPELINES: str = [
    "annotated",
    "negation",
    "antonyms",
    "synonyms",
]


class Preprocessor:
    @classmethod
    def process_dataset(
        cls,
        language: str,
        model: str | None,
        pipeline: str,
        dataset_path: str,
        file_suffix: str,
        desc: str | None = None,
        tqdm_position: int = 0,
    ):
        dataset_path = Path(dataset_path)
        file_path = dataset_path / f"{language}_{file_suffix}.json"
        if (file_path).exists():
            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as f:
                preprocessed_dataset = json.load(f)
        else:
            preprocessed_dataset = []
        with open(
            (
                dataset_path / f"{language}.json"
                if file_suffix == "annotated"
                else dataset_path / f"{language}_annotated.json"
            ),
            encoding="utf-8",
        ) as f:
            dataset = json.load(f)
        # Already processed?
        if len(preprocessed_dataset) == len(dataset):
            return
        dataset = dataset[len(preprocessed_dataset) :].copy()
        for sample in tqdm(dataset, desc=desc, position=tqdm_position):
            preprocessed_dataset.append(
                {
                    "origin": sample["origin"],
                    "global_id": sample["global_id"],
                    "type_id": sample["type_id"],
                    "type": sample["type"],
                    "question_id": sample["question_id"],
                    "question": cls.process_sample(
                        sample["question"], pipeline, language, model
                    ),
                }
            )
            # We save at every iteration (inefficient but we don't lose data :)
            with open(
                file_path,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(preprocessed_dataset, f, ensure_ascii=False, indent=4)

    @classmethod
    @abstractmethod
    def process_sample(
        cls,
        prompt: str,
        pipeline: str,
        language: str,
        model: str | None,
        **kwargs,
    ):
        pass


class LLMPreprocessor(Preprocessor):
    @classmethod
    def process_sample(
        cls,
        prompt: str,
        pipeline: str,
        language: str,
        model: str | None,
        **kwargs,
    ):
        prompt_template = None
        match pipeline:
            case "annotated":
                prompt_template = Prompt.PREPROCESS.IDENTIFY_HARMFUL
            case "negation":
                prompt_template = Prompt.PREPROCESS.NEGATE_TEXT
            case "antonyms":
                prompt_template = Prompt.PREPROCESS.REPLACE_WITH_ANTONYM
            case "synonyms":
                prompt_template = (Prompt.PREPROCESS.REPLACE_WITH_SYNONYM,)
            case _:
                raise NotImplementedError(f"pipeline {pipeline} not supported")
        prompt = populate_prompt_template(
            getattr(prompt_template, language.upper()),
            prompt,
        )
        conversation = [{"role": "user", "content": prompt}]
        return inference(model, conversation).strip('"')


class Pipeline(ABC):
    def __init__(
        self,
        model: str,
        language: str,
        dataset_path: str,
        output_path: str,
        pipeline_name: str,
    ):
        self.model = model
        self.language = language
        self.output_path = Path(output_path)

        self.dataset_path = Path(dataset_path)
        self.dataset = None

        self.pipeline_name = pipeline_name

        # Drop reasoning effort if not supported by model.
        litellm.drop_params = True

    def add_conversation_round(self, conversation, new_prompt) -> dict:
        conversation.append({"role": "user", "content": new_prompt})

        for _ in range(5):
            try:
                response = completion_without_reasoning(
                    model=self.model,
                    messages=conversation,
                ).model_dump(mode="json")
                if response:
                    break
            except (APIError, BadRequestError) as ex:
                if (
                    ex.llm_provider == "xai" and "SAFETY_CHECK_TYPE_BIO" in ex.message
                ):  # Grok safety check
                    response = "I cannot assist with that."
                time.sleep(1)

        conversation.append({"role": "assistant", "content": response})
        return conversation

    @abstractmethod
    def run(self, **kwargs):
        pass

    def _run(
        self,
        prompt_template: str,
        directory_name: str,
        tqdm_desc: str | None = None,
        tqdm_position: int = 0,
    ):
        # Create the directory structure.
        full_output_path = (
            self.output_path / directory_name / self.model / self.language
        )
        full_output_path.mkdir(parents=True, exist_ok=True)

        # Iterate through prompts.
        for sample in tqdm(
            self.dataset,
            desc=tqdm_desc,
            position=tqdm_position,
        ):
            # Check if output file already exists
            output_file = full_output_path / f"{sample["global_id"]:04d}.json"
            if Path(output_file).is_file():
                # print(f"Output file {output_file} already exists. Skipping.")
                continue

            if not isinstance(prompt_template, str):
                prompt_template = getattr(
                    prompt_template,
                    self.language.upper(),
                )
            processed_prompt = populate_prompt_template(
                prompt_template,
                (
                    sample["question_corrected"]
                    if "question_corrected" in sample
                    else sample["question"]
                ),
            )

            conversation = self.add_conversation_round([], processed_prompt)
            if (
                conversation[-1]["content"]["choices"][0].get("finish_reason")
                == "refusal"
            ):
                conversation[-1]["content"]["choices"][0]["message"][
                    "content"
                ] = "I cannot assist with that."

            output = {
                "id": sample["global_id"],
                "origin": sample["origin"],
                "type": sample["type"],
                "conversation": conversation,
            }

            # Save to JSON.
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)

    def load_dataset(self, file_suffix: str | None):
        path = f"{self.language}_{file_suffix}.json" if file_suffix else f"{self.language}.json"
        with open(
            self.dataset_path / path,
            "r",
            encoding="utf-8",
        ) as f:
            self.dataset = json.load(f)


class AsIsPipeline(Pipeline):
    def __init__(
        self,
        model: str,
        language: str,
        dataset_path: str,
        output_path: str,
    ):
        pipeline_name: str = "as_is"
        super().__init__(model, language, dataset_path, output_path, pipeline_name)
        self.load_dataset(file_suffix=None)

    def run(self, **kwargs):
        tqdm_position = kwargs.get("tqdm_position")
        super()._run(
            prompt_template=Prompt.VARIATION.AS_IS,
            directory_name="as_is",
            tqdm_desc=f"{self.language}: As-Is inference ({self.model.split('/')[-1]})",
            tqdm_position=tqdm_position,
        )


class NegationPipeline(Pipeline):
    def __init__(
        self,
        model: str,
        language: str,
        dataset_path: str,
        output_path: str,
    ):
        pipeline_name: str = "negation"
        super().__init__(model, language, dataset_path, output_path, pipeline_name)
        self.load_dataset(file_suffix=pipeline_name)

    def run(self, **kwargs):
        with_wrapper = kwargs.get("with_wrapper")
        tqdm_position = kwargs.get("tqdm_position")
        super()._run(
            prompt_template=(
                Prompt.VARIATION.NEGATED_WRAPPER if with_wrapper else Prompt.VARIATION.NEGATED
            ),
            directory_name="negation_wrapper" if with_wrapper else "negation",
            tqdm_desc=(
                f"{self.language}: Negation inference"
                f" {'(wrapper)' if with_wrapper else ''} ({self.model.split('/')[-1]})"
            ),
            tqdm_position=tqdm_position,
        )


class AntonymPipeline(Pipeline):
    def __init__(
        self,
        model: str,
        language: str,
        dataset_path: str,
        output_path: str,
    ):
        pipeline_name: str = "antonyms"
        super().__init__(model, language, dataset_path, output_path, pipeline_name)
        self.load_dataset(file_suffix=pipeline_name)

    def run(self, **kwargs):
        with_wrapper = kwargs.get("with_wrapper")
        tqdm_position = kwargs.get("tqdm_position")
        super()._run(
            prompt_template=(
                Prompt.VARIATION.ANTONYM_WRAPPER if with_wrapper else Prompt.VARIATION.ANTONYM
            ),
            directory_name="antonym_wrapper" if with_wrapper else "antonym",
            tqdm_desc=(
                f"{self.language}: Antonym inference"
                f" {'(wrapper)' if with_wrapper else ''} ({self.model.split('/')[-1]})"
            ),
            tqdm_position=tqdm_position,
        )


class SynonymPipeline(Pipeline):
    def __init__(
        self,
        model: str,
        language: str,
        dataset_path: str,
        output_path: str,
    ):
        pipeline_name: str = "synonyms"
        super().__init__(model, language, dataset_path, output_path, pipeline_name)
        self.load_dataset(file_suffix=pipeline_name)

    def run(self, **kwargs):
        with_wrapper = kwargs.get("with_wrapper")
        tqdm_position = kwargs.get("tqdm_position")
        super()._run(
            prompt_template=(
                Prompt.VARIATION.SYNONYM_WRAPPER if with_wrapper else Prompt.VARIATION.SYNONYM
            ),
            directory_name="synonym_wrapper" if with_wrapper else "synonym",
            tqdm_desc=(
                f"{self.language}: Synonym inference"
                f" {'(wrapper)' if with_wrapper else ''} ({self.model.split('/')[-1]})"
            ),
            tqdm_position=tqdm_position,
        )
