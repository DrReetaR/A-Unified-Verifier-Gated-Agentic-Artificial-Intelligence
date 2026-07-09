# First-Person Grammar Checker

Detects first-person constructions (`we`, `our`, `us`, `I`, `my`, contractions,
`let us`, `allows us to`, ...) and rephrases sentences into impersonal, academic
voice. Rule-based and deterministic — no external models.

## Usage
```python
from firstperson_cleaner import check, rephrase, has_first_person

rephrase("In this paper, we propose a framework. Our results improve accuracy.")
# -> "This paper proposes a framework. The results improve accuracy."

rep = check("We evaluate our model.")
rep.cleaned    # "This work evaluates the model."
rep.is_clean   # True
rep.issues     # [Issue('We',...), Issue('our',...)]
```

CLI:
```bash
python firstperson_cleaner.py "We show that our method works."
```

## Tests
```bash
pytest -v test_firstperson_cleaner.py   # 55 cases
```
Covers detection, false-positive safety (`focus`, `hour`, `your`, `Iterative`),
verb conjugation, gerunds, possessives, contractions, imperative rewrite of
`let us`, `allows us to` -> gerund, clause-boundary agreement, capitalization,
completeness (no first person remains), idempotency, and the `check()` API.
