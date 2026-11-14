We study **3 languages** (English, Spanish, Czech) and two main probes,
**negation** and **antonym**, which reverse the polarity of the malicious
prompt, but at different linguistic levels: the negation probe operates at the
surface, grammatical level, while the antonym probe operates at the
lexicosemantic level.

**Synonym substitution** provides as the polarity preserving control.
Furthermore, each prompt variant (including the original prompt) is evaluated
with and without an **adversarial wrapper**.

<p class="mb-0">
    This setup yields 8 different prompt variants:
</p>

<figure>
  <img
    src="/assets/img/prompt-variations.svg"
    alt="Prompt variations"
    class="w-full sm:w-auto sm:h-110 rounded-lg dark:hidden"
    />
  <img
    src="/assets/img/prompt-variations-dark.svg"
    alt="Prompt variations"
    class="w-full sm:w-auto sm:h-110 rounded-lg hidden dark:block"
    />
  <figcaption class="sm:text-center">Flow diagram with the 8 prompt variations
we evaluate.</figcaption>
</figure>

We evaluate **10 models**—8 closed-weight and 2 open-weight—spanning a range of
sizes, architectures and providers: Grok 4.1 (fast, non-reasoning), GPT-5 (nano
and mini versions), GPT-5.2, Gemini 2.5 (flash and flash lite versions), Claude
Sonnet 4.5, DeepSeek-V3.2, Ministral 3 14B, and Gemma 3 (27b version).

For the harm evaluation, we use a human-validated **LLM-as-a-Judge** (Kimi K2.5)
and report **harm scores** on a **scale 0-5**. Each inference and evaluation is
run
**3 times**, to account for stochasticity. Across 3 languages, 10 models, 8
variants, and 260 prompts, we perform **187,200 inferences**, and the same
number of evaluations.
