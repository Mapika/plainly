"""One-shot: convert the Brysbaert et al. (2014) concreteness norms to a slim CSV.

Source dataset (freely available, ~40k lemmas):
  Brysbaert, Warriner & Kuperman (2014), "Concreteness ratings for 40 thousand
  generally known English word lemmas", Behavior Research Methods.
Input: the tab-delimited 'Concreteness_ratings_Brysbaert_et_al_BRM.txt' (columns
  include 'Word' and 'Conc.M'). Place it next to this script before running.
Output: data/concreteness.csv with two columns: word,conc (rounded to 2dp).
"""
import csv
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "Concreteness_ratings_Brysbaert_et_al_BRM.txt")
OUT = os.path.join(HERE, "data", "concreteness.csv")


def main():
    rows = []
    with open(SRC, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for r in reader:
            word = (r.get("Word") or "").strip().lower()
            try:
                conc = float(r["Conc.M"])
            except (KeyError, ValueError):
                continue
            if word:
                rows.append((word, round(conc, 2)))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["word", "conc"])
        w.writerows(sorted(rows))
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
