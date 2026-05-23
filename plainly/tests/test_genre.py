from plainly.scan import scan
from plainly.config import load_config


def _cfg(genre):
    c = load_config(None)
    c["genre"]["default"] = genre
    return c


MARKETING_TELL = [{"term": "synergy", "weight": 2, "tier": "current", "register": "marketing"}]
GENERAL_TELL = [{"term": "synergy", "weight": 2, "tier": "current"}]


def _weight(text, genre, lexical):
    findings = scan(text, _cfg(genre), patterns=[], lexical=lexical)["findings"]
    return sum(f["weight"] for f in findings)


def test_marketing_tell_scales_down_outside_marketing_genre():
    text = "We chase synergy."
    assert _weight(text, "marketing", MARKETING_TELL) == 2.0   # x1.0
    assert _weight(text, "prose", MARKETING_TELL) == 1.0       # x0.5
    assert _weight(text, "docs", MARKETING_TELL) == 0.5        # x0.25


def test_general_tell_unaffected_by_genre():
    text = "We chase synergy."
    full = 2
    assert _weight(text, "marketing", GENERAL_TELL) == full
    assert _weight(text, "prose", GENERAL_TELL) == full
    assert _weight(text, "docs", GENERAL_TELL) == full


def test_marketing_slop_scores_higher_in_marketing_genre_than_docs():
    # Real data path: announcement + buzzword + emoji tells, register=marketing.
    slop = "We're thrilled to announce our launch. We'll double down on synergy. 🚀"
    mkt = scan(slop, _cfg("marketing"))["density"]
    docs = scan(slop, _cfg("docs"))["density"]
    assert mkt > docs > 0
