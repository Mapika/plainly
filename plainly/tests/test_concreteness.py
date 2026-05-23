from plainly.concreteness import load_lexicon, paragraph_concreteness


def test_abstract_paragraph_scores_low():
    lex = load_lexicon()
    abstract = "We leverage synergy to drive impactful abstraction and commitment."
    concrete = "The dog knocked the glass off the table in the rain."
    a = paragraph_concreteness(abstract, lex)
    c = paragraph_concreteness(concrete, lex)
    assert a["mean_conc"] < c["mean_conc"]
    assert a["coverage"] > 0


def test_empty_returns_zero_coverage():
    assert paragraph_concreteness("", load_lexicon())["coverage"] == 0
