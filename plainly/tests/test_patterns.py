from plainly.patterns import load_patterns, load_lexical, match_patterns, match_lexical


def test_antithesis_detected():
    findings = match_patterns("It's not just a tool, it's a movement.", load_patterns())
    ids = {f["id"] for f in findings}
    assert "antithesis-not-just" in findings[0]["id"] or "antithesis-not-just" in ids


def test_participle_tail_detected():
    findings = match_patterns(
        "We opened offices, underscoring our commitment.", load_patterns()
    )
    assert any(f["id"] == "participle-tail" for f in findings)


def test_no_false_positive_on_clean_sentence():
    findings = match_patterns("The cat sat on the mat.", load_patterns())
    assert findings == []


def test_lexical_hit_carries_weight_and_line():
    text = "First line.\nWe must leverage synergies."
    findings = match_lexical(text, load_lexical())
    hit = next(f for f in findings if f["term"] == "leverage")
    assert hit["line"] == 2
    assert hit["weight"] == 2


def test_stemmed_entries_catch_inflections():
    text = "We are leveraging synergy and transforming workflows."
    findings = match_lexical(text, load_lexical())
    terms = {f["term"] for f in findings}
    assert "leverage" in terms, "stemmed 'leverage' should match 'leveraging'"
    assert "transform" in terms, "stemmed 'transform' should match 'transforming'"


def test_non_stem_entry_does_not_match_inflection():
    # "moreover" has no stem:true, so "moreovering" should NOT match
    text = "We are moreovering our approach."
    findings = match_lexical(text, load_lexical())
    terms = {f["term"] for f in findings}
    assert "moreover" not in terms, "non-stemmed 'moreover' should not match 'moreovering'"


def test_announcement_cliche_detected():
    findings = match_patterns("We're thrilled to announce our launch.", load_patterns())
    assert any(f["id"] == "announcement-cliche" for f in findings)


def test_puffery_significance_detected():
    findings = match_patterns("The cache plays a pivotal role in throughput.", load_patterns())
    assert any(f["id"] == "puffery-significance" for f in findings)


def test_emoji_measured_and_hype_detected():
    ids = {f["id"] for f in match_patterns("Done ✅ and we shipped 🚀", load_patterns())}
    assert "emoji-measured" in ids
    assert "emoji-hype" in ids


def test_emoji_bullet_detected():
    findings = match_patterns("🚀 Fast setup\n✅ Tested\n", load_patterns())
    assert any(f["id"] == "emoji-bullet" for f in findings)


def test_new_ai_vocab_lexical_matches():
    terms = {f["term"] for f in match_lexical("An intricate, meticulous design.", load_lexical())}
    assert "intricate" in terms
    assert "meticulous" in terms


def test_marketing_buzzword_carries_register():
    findings = match_lexical("We chase synergy.", load_lexical())
    hit = next(f for f in findings if f["term"] == "synergy")
    assert hit["register"] == "marketing"
