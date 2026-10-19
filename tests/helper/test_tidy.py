from pictalog_helper.tidy import tidy

# Each case is a slip qwen3.5:4b made reading scripts/eval_languages.py's lists.


def test_a_colour_given_as_the_size_becomes_the_colour():
    assert tidy({"name": "सूती साड़ी", "size": "लाल", "colour": "Red"}) == {"name": "सूती साड़ी", "colour": "लाल"}
    assert tidy({"name": "பருத்திப் புடவை", "size": "சிவப்பு"}) == {"name": "பருத்திப் புடவை", "colour": "சிவப்பு"}
    assert tidy({"name": "Saree", "size": "Red"}) == {"name": "Saree", "colour": "Red"}
    assert tidy({"name": "Kurta", "size": "M", "colour": "Blue"}) == {"name": "Kurta", "size": "M", "colour": "Blue"}
    assert tidy({"name": "Kurta", "size": "लाल", "colour": "नीला"}) == {"name": "Kurta", "size": "लाल", "colour": "नीला"}


def test_the_colour_size_or_price_repeated_at_the_end_of_the_name_is_taken_off():
    assert tidy({"name": "सुती साडी, लाल", "colour": "लाल"}) == {"name": "सुती साडी", "colour": "लाल"}
    assert tidy({"name": "నూలు చీర, ఎరుపు", "price_text": "₹1,450"}) == {
        "name": "నూలు చీర", "price_text": "₹1,450", "colour": "ఎరుపు",
    }
    assert tidy({"name": "चहा पावडर — 250 ग्रॅम", "size": "250 ग्रॅम"})["name"] == "चहा पावडर"
    assert tidy({"name": "ষ্টীলৰ পানীৰ বটল — ১ লিটাৰ", "size": "১ লিটাৰ"})["name"] == "ষ্টীলৰ পানীৰ বটল"
    assert tidy({"name": "पित्तलको दियो — रु. 899", "price_text": "899"})["name"] == "पित्तलको दियो"
    assert tidy({"name": "পিতলের প্রদীপ — ৩৮৯৯", "price_text": "৩৮৯৯"})["name"] == "পিতলের প্রদীপ"


def test_names_that_only_look_like_that_are_kept():
    assert tidy({"name": "T-Shirt — Red", "colour": "Blue"})["name"] == "T-Shirt — Red"
    assert tidy({"name": "iPhone 15", "price_text": "15"})["name"] == "iPhone 15"
    assert tidy({"name": "Rice — 5 kg", "size": "10 kg"})["name"] == "Rice — 5 kg"
    assert tidy({"name": "लाल", "colour": "लाल"})["name"] == "लाल"


def test_a_size_that_lost_its_number_gets_it_back_from_the_name_or_the_list():
    assert tidy({"name": "स्टिलको पानीको बोतल — 1 लिटर", "size": "लिटर"}) == {
        "name": "स्टिलको पानीको बोतल", "size": "1 लिटर",
    }
    page = "எவர்சில்வர் தண்ணீர் பாட்டில் — 1 லிட்டர் — ₹350\nடீ தூள் — 250 கிராம் — ரூ. 120"
    assert tidy({"name": "எவர்சில்வர் தண்ணீர் பாட்டல்", "size": "லிட்டர்"}, page)["size"] == "1 லிட்டர்"
    assert tidy({"name": "டீ தூள்", "size": "கிராம்"}, page)["size"] == "250 கிராம்"


def test_a_size_number_is_only_taken_from_the_product_s_own_line():
    page = "Tea — 250 g — ₹120\nCoffee — 500 g — ₹300"
    assert tidy({"name": "Sugar", "size": "g"}, page)["size"] == "g"
    assert tidy({"name": "Coffee", "size": "g"}, page)["size"] == "500 g"


def test_a_material_taken_off_the_front_of_the_name_is_put_back():
    page = "स्टील की पानी की बोतल — 1 लीटर — ₹350\nपीतल का दीया — ₹899\nलाल सूती साड़ी — ₹1,450"
    assert tidy({"name": "पानी की बोतल", "material": "स्टील"}, page)["name"] == "स्टील की पानी की बोतल"
    assert tidy({"name": "दीया", "material": "पीतल"}, page)["name"] == "पीतल का दीया"
    assert tidy({"name": "सूती साड़ी", "colour": "लाल"}, page)["name"] == "सूती साड़ी"  # a colour in front is a variant
    two = "पीतल का दीया — ₹899\nमिट्टी का दीया — ₹40"
    assert tidy({"name": "दीया"}, two)["name"] == "दीया"  # which one?


def test_an_english_material_or_colour_goes_back_into_the_list_s_language():
    assert tidy({"name": "पीतल का दीया", "material": "Brass"})["material"] == "पीतल"
    assert tidy({"name": "સ્ટીલની પાણીની બોટલ", "material": "Steel"})["material"] == "સ્ટીલ"
    assert tidy({"name": "लाल साड़ी", "colour": "Red"})["colour"] == "लाल"
    assert tidy({"name": "Brass Diya", "material": "Brass"})["material"] == "Brass"
    assert tidy({"name": "सूती साड़ी", "material": "Silk"})["material"] == "Silk"
