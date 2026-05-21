## Polarity Blindness in LLM Safety: A Systematic Study of Negation, Antonym Substitution, and Adversarial Framing

### Preparation 

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
