# Papers (LaTeX)

One subdirectory per paper. The agent never edits files in [../paper-templates/](../paper-templates/) directly. Instead, it copies the chosen starter into a new directory here and works on the copy.

## Naming convention

`{template}_{short-paper-title}`

- `{template}` matches one of `ieee-latex`, `mdpi-latex`, `easychair-latex`.
- `{short-paper-title}` is a kebab-case slug of the paper, three to five words at most. Use the same slug as the paired experiment directory under [../experiments/](../experiments/).

Examples:

```text
ieee-latex_modi-detector
mdpi-latex_fbs-survey
easychair-latex_passive-fbs-audit
```

## Per-paper layout

Each paper directory mirrors the chosen template, plus the paper's own `references.bib` populated from notes in [../references/](../references/):

```text
papers-latex/ieee-latex_modi-detector/
├── main.tex
├── references.bib
└── figures/                    symlinks or copies from ../../figures-drawio/ exports
```

## Pairing with experiments

Every paper here should have a matching directory at `../experiments/{short-paper-title}/`. The slug after the underscore in the paper folder name must equal the experiment folder name exactly. This keeps reviewers and future-you able to jump from a paper to the code that produced its results without guesswork.
