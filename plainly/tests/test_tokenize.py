from plainly.tokenize import split_sentences, word_count, split_paragraphs, sentence_spans


def test_split_sentences_basic():
    assert split_sentences("Hello world. How are you? Fine!") == [
        "Hello world.",
        "How are you?",
        "Fine!",
    ]


def test_split_sentences_ignores_blank():
    assert split_sentences("One.\n\n  \nTwo.") == ["One.", "Two."]


def test_word_count():
    assert word_count("the quick brown fox") == 4
    assert word_count("  spaced   out  ") == 2
    assert word_count("") == 0


def test_split_paragraphs():
    text = "Para one line one.\nstill one.\n\nPara two."
    assert split_paragraphs(text) == ["Para one line one.\nstill one.", "Para two."]


def test_sentence_spans_have_line_numbers():
    text = "First.\nSecond sentence here.\nThird."
    spans = sentence_spans(text)
    assert spans[0]["text"] == "First."
    assert spans[0]["line"] == 1
    assert spans[1]["line"] == 2
    assert spans[2]["line"] == 3
