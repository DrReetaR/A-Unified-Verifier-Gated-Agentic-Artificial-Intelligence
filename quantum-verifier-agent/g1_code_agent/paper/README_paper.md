# Research Paper Deliverable

- `Verifier_in_the_Loop_Quantum_Code_Agent.pdf`  — final 25-page compiled paper (single column).
- `Verifier_in_the_Loop_Quantum_Code_Agent.docx` — editable Word version.
- `Verifier_in_the_Loop_Quantum_Code_Agent.tex`  — LaTeX source (single-column, Springer-style layout on the article class).
- `figs/` — all figures referenced by the .tex.

## Rebuild the PDF
```
pdflatex Verifier_in_the_Loop_Quantum_Code_Agent.tex
pdflatex Verifier_in_the_Loop_Quantum_Code_Agent.tex   # second pass for refs
```
Requires: amsmath, mathtools, braket, pifont, booktabs, listings, hyperref (standard TeX Live).
