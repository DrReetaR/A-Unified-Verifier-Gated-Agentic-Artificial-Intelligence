"""First-person grammar checker and rephraser for academic writing.

Purpose
-------
Detect first-person constructions ("we", "our", "us", "I", "my", contractions,
"let us", "allows us to", ...) and rephrase sentences into an impersonal,
passive/third-person academic voice suitable for SCI-journal manuscripts.

Public API
----------
find_first_person(text)  -> list[Issue]      # locate every first-person token
has_first_person(text)   -> bool             # quick predicate
rephrase(text)           -> str              # remove/rewrite into impersonal voice
check(text)              -> Report            # issues + cleaned text + is_clean

The transformation is deterministic and rule-based (no external models), so its
behavior is fully testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List

# ---------------------------------------------------------------------------
# 1. Detection
# ---------------------------------------------------------------------------

# Whole-word, case-insensitive first-person markers.
FIRST_PERSON_TOKENS = [
    "we", "us", "our", "ours", "ourselves",
    "i", "me", "my", "mine", "myself",
    "we've", "we're", "we'll", "we'd",
    "i've", "i'm", "i'll", "i'd",
    "let's",
]

# A token like "I" must be matched only as a standalone capital word, not inside
# words; the \b boundaries and the apostrophe handling below take care of that.
_TOKEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in sorted(FIRST_PERSON_TOKENS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


@dataclass
class Issue:
    token: str
    start: int
    end: int


@dataclass
class Report:
    original: str
    cleaned: str
    issues: List[Issue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not has_first_person(self.cleaned)


def find_first_person(text: str) -> List[Issue]:
    """Return every first-person token occurrence in *text*."""
    return [Issue(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def has_first_person(text: str) -> bool:
    """True if *text* still contains any first-person token."""
    return _TOKEN_RE.search(text) is not None


# ---------------------------------------------------------------------------
# 2. Third-person verb conjugation (for subject rewriting)
# ---------------------------------------------------------------------------

_IRREGULAR_3RD = {
    "have": "has",
    "do": "does",
    "go": "goes",
    "be": "is",
}


def third_person(verb: str) -> str:
    """Conjugate a base-form English verb to third-person singular present."""
    v = verb.lower()
    if v in _IRREGULAR_3RD:
        return _IRREGULAR_3RD[v]
    if v.endswith("y") and len(v) > 1 and v[-2] not in "aeiou":
        return v[:-1] + "ies"           # study -> studies
    if v.endswith(("s", "x", "z", "ch", "sh")):
        return v + "es"                 # discuss -> discusses
    if v.endswith("o"):
        return v + "es"                 # echo -> echoes
    return v + "s"                      # propose -> proposes


def gerund(verb: str) -> str:
    """Return the -ing form of a base-form English verb (reduce -> reducing)."""
    v = verb.lower()
    if v.endswith("ie"):
        return v[:-2] + "ying"          # (rare) lie -> lying
    if v.endswith("e") and not v.endswith("ee"):
        return v[:-1] + "ing"           # reduce -> reducing
    return v + "ing"                    # compute stays, run -> runing (simplified)


# ---------------------------------------------------------------------------
# 3. Rephrasing rules
# ---------------------------------------------------------------------------

def _match_case(template_word: str, source_word: str) -> str:
    """Return *template_word* capitalized to mirror *source_word*."""
    return template_word[:1].upper() + template_word[1:] if source_word[:1].isupper() else template_word


def _rule_in_this_paper(text: str) -> str:
    # "In this paper/study/work/article, we <verb> ..." -> "This paper <verb-s> ..."
    pat = re.compile(
        r"\bIn this (paper|study|work|article|research)\s*,?\s+we\s+([a-zA-Z]+)",
        re.IGNORECASE,
    )
    return pat.sub(lambda m: f"This {m.group(1).lower()} {third_person(m.group(2))}", text)


def _rule_allow_enable_us(text: str) -> str:
    # "allows/enables/helps us to VERB" -> "allows/enables/helps VERBing"
    text = re.sub(
        r"\b(allow|allows|enable|enables|let|lets|help|helps)\s+us\s+to\s+([a-zA-Z]+)",
        lambda m: f"{m.group(1)} {gerund(m.group(2))}", text, flags=re.IGNORECASE)
    # bare "allows us <...>" without "to" -> drop the object pronoun
    text = re.sub(r"\b(allow|allows|enable|enables|help|helps)\s+us\b",
                  lambda m: m.group(1), text, flags=re.IGNORECASE)
    return text


def _rule_let_us(text: str) -> str:
    # "Let us consider X" / "Let's consider X" -> "Consider X"
    def repl(m):
        verb = m.group(2)
        return _match_case(verb, m.group(0))
    return re.sub(r"\b(Let us|Let's)\s+([a-zA-Z]+)", repl, text, flags=re.IGNORECASE)


# Clause-boundary cues after which a "we/I + verb" subject may appear.
_CLAUSE_LEAD = r"(^|[.;:]\s|,\s|\b(?:that|which|and|but|where|while|when|so|because|if|then|as|thus|hence|therefore)\s)"


def _rule_subject_verb(text: str) -> str:
    # "We/I <verb> ..." at a clause boundary -> "This work <verb-s> ..."
    def repl(m):
        lead, subj, verb = m.group(1), m.group(2), m.group(3)
        # Preserve capitalization only when the clause starts a sentence.
        starts_sentence = (lead == "") or lead.strip()[-1:] in ".;:"
        subject = _match_case("this work", subj) if starts_sentence else "this work"
        return f"{lead}{subject} {third_person(verb)}"
    pat = re.compile(_CLAUSE_LEAD + r"(We|we|I)\s+([a-zA-Z]+)")
    return pat.sub(repl, text)


def _rule_possessive(text: str) -> str:
    # "our/my X" -> "the X"; "ours/mine" -> "the work's".
    text = re.sub(r"\b(our|my)\b", lambda m: _match_case("the", m.group(1)), text, flags=re.IGNORECASE)
    text = re.sub(r"\b(ours|mine)\b", lambda m: _match_case("the work's", m.group(1)), text, flags=re.IGNORECASE)
    return text


def _rule_contractions(text: str) -> str:
    mapping = [
        (r"\bwe've\b", "this work has"),
        (r"\bwe're\b", "this work is"),
        (r"\bwe'll\b", "this work will"),
        (r"\bwe'd\b", "this work would"),
        (r"\bi've\b", "this work has"),
        (r"\bi'm\b", "this work is"),
        (r"\bi'll\b", "this work will"),
        (r"\bi'd\b", "this work would"),
    ]
    for pat, repl in mapping:
        text = re.sub(pat, lambda m, r=repl: _match_case(r, m.group(0)), text, flags=re.IGNORECASE)
    return text


def _rule_residual(text: str) -> str:
    # Any surviving standalone "we"/"us"/"I"/"me" as clause subject/object.
    text = re.sub(r"(^|(?<=[.;:])\s|(?<=,)\s)(We|I)\b",
                  lambda m: f"{m.group(1)}" + _match_case("this work", m.group(2)), text)
    text = re.sub(r"\b(we|us|me|myself|ourselves)\b",
                  lambda m: _match_case("the work", m.group(1)), text, flags=re.IGNORECASE)
    text = re.sub(r"\b(i)\b",
                  lambda m: _match_case("the author", m.group(1)), text)
    return text


def _tidy(text: str) -> str:
    text = re.sub(r"\s{2,}", " ", text)          # collapse double spaces
    text = re.sub(r"\s+([.,;:])", r"\1", text)   # no space before punctuation
    return text.strip()


_PIPELINE = [
    _rule_in_this_paper,
    _rule_allow_enable_us,
    _rule_let_us,
    _rule_contractions,
    _rule_subject_verb,
    _rule_possessive,
    _rule_residual,
    _tidy,
]


def rephrase(text: str) -> str:
    """Rewrite *text* into impersonal academic voice, removing first person."""
    for rule in _PIPELINE:
        text = rule(text)
    return text


def check(text: str) -> Report:
    """Full report: original issues, cleaned text, and cleanliness flag."""
    issues = find_first_person(text)
    cleaned = rephrase(text)
    return Report(original=text, cleaned=cleaned, issues=issues)


if __name__ == "__main__":
    import sys
    src = " ".join(sys.argv[1:]) or "In this paper, we propose a framework. Our results show that we improve accuracy."
    rep = check(src)
    print("ORIGINAL:", rep.original)
    print("CLEANED :", rep.cleaned)
    print("ISSUES  :", [i.token for i in rep.issues])
    print("IS CLEAN:", rep.is_clean)
