# Data sources and licensing

This evaluation used several third-party datasets. To keep the public repository clean of
redistributed third-party text, the **raw texts from licensed datasets are not committed
here.** What remains is our own generated text, public-domain and CC0 text, and the derived
measurements (`metrics.csv`), which contain numbers — not the source prose. Every result is
reproducible: `../scripts/build_corpus.py` refetches the source data from the links below.

## Removed from the repo (refetch to reproduce)

- **HC3 — Human ChatGPT Comparison Corpus** (`Hello-SimpleAI/HC3`). License: **CC-BY-SA-4.0**.
  We used human and ChatGPT answers across general, QA, finance, and medicine.
  https://huggingface.co/datasets/Hello-SimpleAI/HC3
- **ChatGPT-Research-Abstracts** (Nicolai Thorer Sivesind, 2023). License: Creative Commons
  (variant unspecified). Real abstracts paired with GPT-3.5-generated abstracts.
  https://huggingface.co/datasets/NicolaiSivesind/ChatGPT-Research-Abstracts

The corresponding rows still appear in `metrics.csv` (as `*_hc3_*` and `*_sciabs_*` ids) so
the statistics reproduce, but the prose itself is not stored here.

## Kept in the repo

- **arXiv abstracts** fetched via the arXiv API (`corpus/human/h_arxiv_*`) and the sample
  abstracts in `../samples/human/arxiv-*.md`. arXiv descriptive metadata, including
  abstracts, is released under **CC0 1.0** (public domain) — free to redistribute.
  https://info.arxiv.org/help/api/tou.html
- **Blind-writer generations** (`corpus/ai/blind_*`) and the OpenRouter experiment outputs
  (`../experiment/out/`) — text we generated from models we prompted.
- **Public-domain literary excerpts** in `../samples/human/`: Mark Twain (*Roughing It*),
  Thoreau (*Walden*), Jerome K. Jerome (*Three Men in a Boat*), Franklin (*Autobiography*),
  and the King James Bible. All public domain.
- **`../samples/human/wikipedia-octopus.md`** — adapted from the English Wikipedia article
  "Giant Pacific octopus," licensed **CC-BY-SA-4.0** (attribution: Wikipedia contributors).
- **`../samples/human/orwell.md`** — a short quotation from George Orwell, "Politics and the
  English Language" (1946), used for commentary/research.
- **`../samples/ai/`** — short illustrative AI-style passages written by the project authors.

## Note on licenses

The repository code is MIT. The retained third-party text keeps its own license (CC0 for
arXiv; CC-BY-SA-4.0 for the Wikipedia excerpt, attributed above). Concreteness data: the full
Brysbaert et al. (2014) lexicon is not bundled; see `../../plainly/scripts/build_concreteness.py`.
