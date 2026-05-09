# TSP (Tech Science Press) LaTeX Template

Starter for journals published by Tech Science Press, including *Computers, Materials & Continua (CMC)*, *Computer Modeling in Engineering & Sciences (CMES)*, *Journal of Cyber Security (JCS)*, *Journal of Information Hiding and Privacy Protection (JIHPP)*, and others.

The template ships with the bundled class file (`Definitions/tsp.cls`), package preamble (`Definitions/package.tex`), unicode handling (`Definitions/unicode.tex`), Vancouver bibliography style (`Definitions/vancouver.bst`), the journal name list (`Definitions/journalnames.tex`), and the TSP logos required by the title page.

## Files

- `main.tex` — manuscript skeleton, edit the `\Title`, `\Author`, `\address`, `\corres`, `\abstract`, and `\keyword` fields before drafting
- `references.bib` — empty bibliography, populate from `../../references/` markdown notes
- `Definitions/` — class file and supporting assets, do not modify

## Choosing the journal

Read the comment block at the top of `main.tex` for the list of journal codes accepted by `\documentclass[journal,...]{Definitions/tsp}`. Replace the default with the target journal's code (for example, `cmc` for *Computers, Materials & Continua*).

## Article type

Default is `article`. Replace with one of the types listed in the comment block (`review`, `mini review`, `short communication`, `tutorial`, etc.) when submitting a non-research-article manuscript.

## Submit vs accept

The class option `submit` produces the submission-ready front page with line numbering. The editorial office flips it to `accept` on acceptance, which adds the journal logo and removes line numbers. Do not change this option manually.
