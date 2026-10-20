## Polarity Blindness in LLM Safety: A Systematic Study of Negation, Antonym Substitution, and Adversarial Framing
#### _Diego Miguel Lozano, Erik Derner, Juan Antonio Pérez-Ortiz, Nuria Oliver_

Abstract:
> _Negation remains a persistent challenge for language models across NLP tasks and modalities. We show that this weakness can undermine LLM safety guardrails through a structural vulnerability we term polarity blindness: the failure to recognize harmful intent after polarity-altering linguistic transformations. We study two forms of polarity inversion: grammatical negation and antonym replacement, and use synonym replacement as a polarity-preserving control. We further test whether an adversarial textual wrapper amplifies these failures. Using a 260-prompt benchmark across 10 state-of-the-art LLMs and 3 languages (English, Spanish, Czech), stratified by harmfulness potential and evaluated on a validated 0–5 harm scale, we find that polarity blindness affects most evaluated models, with mean harm scores reaching 4.12 for the most vulnerable model. The effect persists across typologically differing negation systems, suggesting that polarity blindness reflects a broader limitation in semantic robustness rather than a language- or grammar-specific failure._

<br>

## Data

You can find the benchmark under [`benchmark/`](https://github.com/dmlls/llm-safety-polarity-blindness/tree/main/benchmark).

```
├── <lang>_annotated.json  -> base queries ("as-is")
├── <lang>_negation.json   -> negated queries
├── <lang>_antonyms.json   -> replacement with antonyms
└── <lang>_synonyms.json   -> replacement with synonyms
```

`en_annotated.json` also contains the harmfulness potential annotations (`harmfulness_rating`).

<br>

## Code

### Installation 

First, install the project dependencies with:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

<br>

### Running the experiments

Navigate to the `code/` directory.

Configure the experiments (pipelines) you want to run in `config.yml`. Here you can also configure other parameters of the experiment and evaluation.

Create a `.env` file following the structure of `env-example`. Include your API keys in the file.

Then, simply execute:

```
python run_experiment.py
```
<br>

### Evaluating

Run:

```
python evaluate.py
```

You can set the judge model in `config.yml`.
