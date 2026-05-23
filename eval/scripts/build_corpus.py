#!/usr/bin/env python3
"""Build a labeled human-vs-AI text corpus from already-downloaded source files.

Stdlib only. Sources (downloaded separately via curl/urllib):
  - HC3 all.jsonl  (Hello-SimpleAI/HC3): human_answers vs chatgpt_answers across
    domains: reddit_eli5(general), open_qa+wiki_csai(qa), finance, medicine.
  - ChatGPT-Research-Abstracts CSV (NicolaiSivesind): real_abstract(human) vs
    generated_abstract(GPT-3.5) -> scientific register.
  - arXiv API pre-2022 abstracts -> extra clearly-human scientific samples
    (fetched live here with urllib).

Cleaning: strip simple markup/whitespace, keep 40<=words<=400.
Writes texts to eval/data/corpus/<label>/<id>.txt and returns a manifest list.
"""
import csv
import html
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = os.path.join(ROOT, "eval/data/corpus")
HC3 = "/tmp/hc3_test.json"
ABS_CSV = "/tmp/research_abstracts.csv"

MIN_WORDS, MAX_WORDS = 40, 400

# Per-source caps to keep classes balanced and domains diverse.
HC3_DOMAIN_MAP = {
    "reddit_eli5": "general",
    "open_qa": "qa",
    "wiki_csai": "qa",
    "finance": "finance",
    "medicine": "medicine",
}
# how many PAIRS (1 human + 1 ai each) to take per HC3 domain
HC3_PAIRS_PER_DOMAIN = {
    "general": 12,
    "qa": 12,
    "finance": 10,
    "medicine": 10,
}
SCI_PAIRS = 18          # paired human/ai scientific abstracts
ARXIV_HUMAN = 8         # extra human-only scientific abstracts


def clean(text):
    if not text:
        return ""
    t = html.unescape(text)
    t = re.sub(r"`{1,3}", "", t)            # code ticks
    t = re.sub(r"[*_#>]+", " ", t)          # md markup
    t = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", t)  # md links
    t = re.sub(r"https?://\S+", "", t)      # urls
    t = re.sub(r"\s+", " ", t).strip()
    # HC3 has space-padded tokens like " 's" and " ?"; tidy common cases
    t = re.sub(r"\s+([.,;:!?%])", r"\1", t)
    t = re.sub(r"\(\s+", "(", t)
    t = re.sub(r"\s+\)", ")", t)
    return t


def wc(t):
    return len(t.split())


def ok(t):
    n = wc(t)
    return MIN_WORDS <= n <= MAX_WORDS


def write_text(label, idx, text):
    d = os.path.join(CORPUS, label)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, idx + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return path


def build_hc3(rows):
    # group HC3 records by mapped domain
    by_domain = {}
    with open(HC3, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            dom = HC3_DOMAIN_MAP.get(r.get("source"))
            if not dom:
                continue
            by_domain.setdefault(dom, []).append(r)
    for dom, want in HC3_PAIRS_PER_DOMAIN.items():
        recs = by_domain.get(dom, [])
        taken = 0
        for i, r in enumerate(recs):
            if taken >= want:
                break
            ha = [clean(a) for a in (r.get("human_answers") or [])]
            ca = [clean(a) for a in (r.get("chatgpt_answers") or [])]
            h = next((a for a in ha if ok(a)), None)
            a = next((c for c in ca if ok(c)), None)
            if not (h and a):
                continue
            base = "hc3_%s_%04d" % (dom, i)
            hp = write_text("human", "h_" + base, h)
            ap = write_text("ai", "a_" + base, a)
            rows.append(dict(id="h_" + base, label="human", domain=dom,
                             source="HC3", path=hp, n_words=wc(h)))
            rows.append(dict(id="a_" + base, label="ai", domain=dom,
                             source="HC3", path=ap, n_words=wc(a)))
            taken += 1
        print("HC3 %-9s pairs=%d" % (dom, taken), file=sys.stderr)


def build_sci(rows):
    taken = 0
    with open(ABS_CSV, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for i, r in enumerate(rd):
            if taken >= SCI_PAIRS:
                break
            h = clean(r.get("real_abstract"))
            a = clean(r.get("generated_abstract"))
            if not (ok(h) and ok(a)):
                continue
            base = "sciabs_%04d" % i
            hp = write_text("human", "h_" + base, h)
            ap = write_text("ai", "a_" + base, a)
            rows.append(dict(id="h_" + base, label="human", domain="scientific",
                             source="ChatGPT-Research-Abstracts", path=hp, n_words=wc(h)))
            rows.append(dict(id="a_" + base, label="ai", domain="scientific",
                             source="ChatGPT-Research-Abstracts", path=ap, n_words=wc(a)))
            taken += 1
    print("SCI pairs=%d" % taken, file=sys.stderr)


def build_arxiv(rows):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    cats = ["cs.LG", "q-bio.NC", "stat.ME"]
    taken = 0
    for cat in cats:
        if taken >= ARXIV_HUMAN:
            break
        url = ("http://export.arxiv.org/api/query?search_query=cat:%s+AND+"
               "submittedDate:[201901010000+TO+202012312359]&start=0&"
               "max_results=6&sortBy=submittedDate&sortOrder=ascending" % cat)
        try:
            data = urllib.request.urlopen(url, timeout=30).read()
        except Exception as e:
            print("arXiv %s failed: %s" % (cat, e), file=sys.stderr)
            continue
        root = ET.fromstring(data)
        for j, e in enumerate(root.findall("a:entry", ns)):
            if taken >= ARXIV_HUMAN:
                break
            elem = e.find("a:summary", ns)
            summ = clean(elem.text if elem is not None else "")
            if not ok(summ):
                continue
            base = "arxiv_%s_%d" % (cat.replace(".", ""), j)
            hp = write_text("human", "h_" + base, summ)
            rows.append(dict(id="h_" + base, label="human", domain="scientific",
                             source="arXiv-API-pre2022", path=hp, n_words=wc(summ)))
            taken += 1
        time.sleep(3)  # be polite to arXiv API
    print("arXiv human=%d" % taken, file=sys.stderr)


def main():
    rows = []
    build_hc3(rows)
    build_sci(rows)
    build_arxiv(rows)
    # persist intermediate manifest of rows for the metrics step
    with open("/tmp/corpus_rows.json", "w") as f:
        json.dump(rows, f)
    h = sum(1 for r in rows if r["label"] == "human")
    a = sum(1 for r in rows if r["label"] == "ai")
    print("TOTAL human=%d ai=%d total=%d" % (h, a, len(rows)), file=sys.stderr)


if __name__ == "__main__":
    main()
