from leadpipe.normalize import dedupe_key, extract_zip, normalize_address, normalize_name


def test_normalize_name_strips_suffix_and_punctuation():
    assert normalize_name("Northstar Dental, LLC") == "northstar dental"
    assert normalize_name("The Lakes P.T. Inc.") == "lakes p t"
    assert normalize_name("Smith & Jones PLLC") == "smith and jones"
    assert normalize_name("") == ""


def test_normalize_address_abbreviates():
    assert (
        normalize_address("250 Marquette Avenue South, Suite 300") == "250 marquette ave s ste 300"
    )
    assert normalize_address("250 MARQUETTE AVE S STE 300") == "250 marquette ave s ste 300"


def test_extract_zip():
    assert extract_zip("Eagan, MN 55121-1234") == "55121"
    assert extract_zip("no zip here") == ""
    assert extract_zip("PO Box 123456") == ""


def test_dedupe_key_prefers_name_and_zip():
    assert dedupe_key("Northstar Dental LLC", "55121") == "northstar dental|55121"
    assert dedupe_key("Northstar Dental", "", city="Eagan") == "northstar dental|eagan"
    assert dedupe_key("", "55401", address="250 Marquette Ave") == "@250 marquette ave|55401"
