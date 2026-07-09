"""Test suite for the first-person grammar checker/rephraser.

Run with:  pytest -v test_firstperson_cleaner.py
"""
import pytest

from firstperson_cleaner import (
    find_first_person,
    has_first_person,
    rephrase,
    check,
    third_person,
    gerund,
)

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_tokens", [
    ("We propose a method.", ["We"]),
    ("Our results and my model.", ["Our", "my"]),
    ("This benefits us greatly.", ["us"]),
    ("We're testing our work.", ["We're", "our"]),   # 'We're' not double-counted as 'We'
    ("I evaluate the design.", ["I"]),
    ("It uses mine and ours.", ["mine", "ours"]),
])
def test_find_first_person_detects_tokens(text, expected_tokens):
    assert [i.token for i in find_first_person(text)] == expected_tokens


@pytest.mark.parametrize("clean_text", [
    "The framework improves accuracy.",
    "This study analyzes four datasets in one hour.",   # 'four','hour','one' not flagged
    "The focus is thus on status and clusters.",         # 'us' inside words not flagged
    "Your results and the author differ.",               # 'Your' not flagged
    "Iterative refinement is applied.",                  # leading 'I' inside word not flagged
])
def test_no_false_positives(clean_text):
    assert has_first_person(clean_text) is False
    assert find_first_person(clean_text) == []


def test_has_first_person_true_and_false():
    assert has_first_person("We show results.") is True
    assert has_first_person("The results are shown.") is False


# ---------------------------------------------------------------------------
# Verb helpers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("base,third", [
    ("propose", "proposes"),
    ("present", "presents"),
    ("study", "studies"),
    ("apply", "applies"),
    ("discuss", "discusses"),
    ("analyze", "analyzes"),
    ("go", "goes"),
    ("have", "has"),
    ("do", "does"),
])
def test_third_person(base, third):
    assert third_person(base) == third


@pytest.mark.parametrize("base,ger", [
    ("reduce", "reducing"),
    ("compute", "computing"),
    ("improve", "improving"),
    ("analyze", "analyzing"),
    ("test", "testing"),
])
def test_gerund(base, ger):
    assert gerund(base) == ger


# ---------------------------------------------------------------------------
# Rephrasing rules (exact expected output)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("src,expected", [
    # subject + verb at sentence start
    ("We propose a novel method.", "This work proposes a novel method."),
    ("I evaluate the design.", "This work evaluates the design."),
    # "In this paper, we ..." pattern
    ("In this paper, we propose a framework.", "This paper proposes a framework."),
    ("In this study, we analyze the data.", "This study analyzes the data."),
    # possessives
    ("Our framework and my analysis improve results.",
     "The framework and the analysis improve results."),
    # ours / mine
    ("The credit is ours.", "The credit is the work's."),
    # contractions
    ("We've shown that the model works.", "This work has shown that the model works."),
    ("We're confident in the outcome.", "This work is confident in the outcome."),
    # let us / let's -> imperative
    ("Let us consider the general case.", "Consider the general case."),
    ("Let's define the objective.", "Define the objective."),
    # allows/enables us to -> gerund
    ("This approach allows us to reduce error.", "This approach allows reducing error."),
    ("The method enables us to compute the state.", "The method enables computing the state."),
    # mid-clause connectors keep agreement
    ("We study parity and we apply it.", "This work studies parity and this work applies it."),
    ("The data show that we improve accuracy.", "The data show that this work improves accuracy."),
])
def test_rephrase_exact(src, expected):
    assert rephrase(src) == expected


def test_capitalization_preserved_at_sentence_start():
    out = rephrase("We present the results.")
    assert out[0].isupper()
    assert out == "This work presents the results."


def test_clean_text_unchanged():
    text = "The proposed framework attains a high pass rate on the benchmark."
    assert rephrase(text) == text


# ---------------------------------------------------------------------------
# Completeness and stability
# ---------------------------------------------------------------------------

PARAGRAPHS = [
    "In this paper, we propose a verifier. Our agent repairs code, and we show it works.",
    "We believe our method is robust; we evaluate it and we report the results.",
    "Let us define the loss. We then minimize it, which allows us to improve accuracy.",
    "I introduce the model. My experiments confirm that I reach the target.",
    "We've built the system, and we're releasing our data so it helps us to reproduce.",
]

@pytest.mark.parametrize("para", PARAGRAPHS)
def test_cleaned_output_has_no_first_person(para):
    cleaned = rephrase(para)
    assert has_first_person(cleaned) is False, cleaned


@pytest.mark.parametrize("para", PARAGRAPHS)
def test_idempotent(para):
    once = rephrase(para)
    assert rephrase(once) == once


# ---------------------------------------------------------------------------
# check() report API
# ---------------------------------------------------------------------------

def test_check_report_fields():
    rep = check("In this paper, we propose X. Our results improve.")
    assert rep.original == "In this paper, we propose X. Our results improve."
    assert [i.token for i in rep.issues] == ["we", "Our"]
    assert rep.is_clean is True
    assert "we" not in rep.cleaned.lower().split()


def test_check_on_already_clean_text():
    rep = check("The system is evaluated on ten tasks.")
    assert rep.issues == []
    assert rep.is_clean is True
    assert rep.cleaned == rep.original


def test_no_double_space_or_space_before_punct():
    out = rephrase("We propose , and we test .")
    assert "  " not in out
    assert " ," not in out and " ." not in out
