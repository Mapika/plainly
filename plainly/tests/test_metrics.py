from plainly.metrics import burstiness, lexical_metrics, opener_entropy, punctuation_rates, load_stopwords


def test_burstiness_uniform_is_low():
    # Four identical-length sentences → CV ~ 0 (AI-like).
    text = "aa bb cc. dd ee ff. gg hh ii. jj kk ll."
    b = burstiness(text)
    assert b["n"] == 4
    assert b["cv"] == 0.0
    assert b["mean_consec_diff"] == 0.0


def test_burstiness_varied_is_higher():
    text = "Short. " + "word " * 30 + ". Tiny. " + "again " * 25 + "."
    b = burstiness(text)
    assert b["cv"] > 0.3
    assert b["mean_consec_diff"] > 5


def test_burstiness_too_few_sentences_returns_none():
    assert burstiness("Only one sentence here.") is None


def test_function_word_ratio_uses_stopwords():
    stops = load_stopwords()
    assert "the" in stops
    m = lexical_metrics("the the the cat", stops)
    assert m["function_word_ratio"] == 0.75


def test_hapax_rate():
    m = lexical_metrics("cat cat dog bird", load_stopwords())
    # unique-once words: dog, bird → 2 of 4 tokens
    assert m["hapax_rate"] == 0.5


def test_opener_entropy_uniform_low():
    # Every sentence opens with "Moreover" → entropy 0.
    text = "Moreover x y. Moreover a b. Moreover c d."
    assert opener_entropy(text) == 0.0


def test_opener_entropy_varied_high():
    text = "Cats run. Dogs bark. Birds fly. Fish swim."
    assert opener_entropy(text) > 1.0


def test_punctuation_rates_em_dash():
    r = punctuation_rates("A — b. C; d. E, f, g, h.")
    assert r["em_dash_per_1k_words"] > 0
    assert r["semicolons"] == 1
