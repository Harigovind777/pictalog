from pictalog_helper.glossary import notes


def test_materials_and_colours_in_india_s_languages():
    assert notes("पीतल का दीया") == ["पीतल = brass"]
    assert notes("பருத்திப் புடவை in சிவப்பு") == ["பருத்திப் = cotton", "சிவப்பு = red"]
    assert notes("سوتی ساڑھی in سرخ.") == ["سوتی = cotton", "سرخ = red"]


def test_endings_are_found_but_short_words_must_match_whole():
    assert notes("पितळेचा दिवा") == ["पितळेचा = brass"]  # पितळ + ेचा, "of brass"
    assert notes("স্টিলের জলের বোতল") == ["স্টিলের = stainless steel"]
    assert notes("पाटा") == []  # not a glossary word with an ending
    assert notes("Brass lamp, red") == []  # English needs no note


def test_colour_names_a_colour_in_any_listed_language_or_english():
    from pictalog_helper.glossary import colour

    assert [colour(w) for w in ("लाल", "சிவப்பு", "سرخ", "Red", " ఎరుపు ")] == ["red"] * 5
    assert colour("पीतल") is None  # brass is a material
    assert colour("लालटेन") is None  # a lantern, not "red" with an ending
    assert colour("1 लीटर") is None


def test_native_finds_the_list_s_own_word_for_an_english_one():
    from pictalog_helper.glossary import native

    assert native("पीतल का दीया", "Brass") == "पीतल"
    assert native("સ્ટીલની પાણીની બોટલ", "Steel") == "સ્ટીલ"  # the word without its ending
    assert native("सूती साड़ी", "Silk") is None
    assert native("Brass Diya", "Brass") is None
