<p class="mb-0">
  <b>Polarity-inverting probes</b> (negation and antonym substitution) achieve the
  <b>highest mean harm scores</b> in 9/10 models in English and Spanish, and 8/10 in
  Czech:
</p>

<figure>
  <img
    src="/assets/img/global-harm-scores.svg"
    alt="Prompt variations"
    class="w-full rounded-lg dark:hidden"
    />
  <img
    src="/assets/img/global-harm-scores-dark.svg"
    alt="Prompt variations"
    class="w-full rounded-lg hidden dark:block"
    />
  <figcaption>
  Harm scores obtained by the different variations. The horizontal lines depict the average harm score for the as is (blue line), negation (red line), antonym (orange line) and synonym (green line) prompts, with and without wrapper. In this plot, we exclude the models Claude 4.5 Sonnet and GPT-5 Nano, which are resistant to polarity blindness.
  </figcaption>
</figure>

<p class="mb-0">
  Grok 4.1 (fast, non-reasoning) is the most vulnerable model, with negation
  variations achieving a mean harm of 4.12 in English, 3.93 in Spanish, and 3.84
  in Czech, while GPT-5 Nano and Claude Sonnet 4.5 remain largely robust.
</p>

<figure>
  <img
    src="/assets/img/radar-plot.svg"
    alt="Prompt variations"
    class="w-full sm:w-auto sm:h-95 mx-auto rounded-lg dark:hidden"
    />
  <img
    src="/assets/img/radar-plot-dark.svg"
    alt="Prompt variations"
    class="w-full sm:w-auto sm:h-95 mx-auto rounded-lg hidden dark:block"
    />
  <figcaption>
  Mean harm scores on a 0–5 harm scale for on the English benchmark queries.
  Most models exhibit polarity blindness as the highest scores are achieved by
  the polarity-inverting variations of the prompts (negation and antonym).
  </figcaption>
</figure>

These results supporting the polarity blindness hypothesis: **safety failures
are driven by polarity inversion rather than lexical perturbation alone.**
