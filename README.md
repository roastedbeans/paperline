# Paper Pipeline

Self-contained workflow for drafting an academic paper end to end. Codifies the rules an AI assistant must follow when writing inside this directory.

## Layout

```text
paper-pipeline/
├── CLAUDE.md                       Workflow rules for Claude Code
├── .cursor/rules/
│   ├── paper-pipeline.mdc          Workflow rules for Cursor
│   └── writing.mdc                 Academic style standard, applies always
├── paper-templates/                Pristine starters, never edited directly
│   ├── ieee-latex/                 IEEEtran starter
│   ├── mdpi-latex/                 MDPI generic starter
│   ├── easychair-latex/            easychair starter
│   └── tsp-latex/                  Tech Science Press starter (bundled tsp.cls)
├── papers-latex/                   Working copies, one per paper
│   └── {template}_{short-title}/   e.g., ieee-latex_modi-detector
├── experiments/                    Paired experiment code, one per paper
│   └── {short-title}/              slug must match the paper folder above
├── figures-drawio/                 .drawio sources for every figure in the paper
│   └── DESIGN_GUIDELINES.md        Mandatory drawio style rules
└── references/                     One Markdown file per candidate paper
```

## Workflow at a glance

1. **Idea** — User states the paper idea in one or two sentences.
2. **Format** — Agent asks: IEEE, MDPI, or EasyChair. No default.
3. **Discovery** — Agent searches OpenAlex and Crossref for relevant prior work, writes one Markdown note per candidate under `references/` with DOI, authors, abstract, and relevance.
4. **Drafting** — Agent copies the chosen template into a working directory, then writes the *introduction first*. Subsequent sections follow only after the introduction is approved.
5. **Style** — Every paragraph follows [.cursor/rules/writing.mdc](.cursor/rules/writing.mdc).
6. **Verification** — Before any commit or submission, every cite key is cross-checked against OpenAlex or Crossref. Mismatches are flagged for human review.

## Reusing the rules globally

To apply these rules outside this directory, choose one of:

- Symlink the files into your global Claude / Cursor configuration:
  - `ln -s $(pwd)/CLAUDE.md ~/.claude/CLAUDE.md`
  - `ln -s $(pwd)/.cursor/rules ~/.cursor/rules/paper-pipeline`
- Or copy the directory as a starting point per project.

## Reference verification reference

OpenAlex API documentation: <https://docs.openalex.org>

Crossref API documentation: <https://www.crossref.org/documentation/retrieve-metadata/rest-api/>

The companion app at [../solo-referencing/](../solo-referencing/) provides a UI over the OpenAlex API and uses the same endpoints.
