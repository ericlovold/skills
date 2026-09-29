def test_footprint_loads_rep_list(footprint):
    assert footprint.contains_zip("55401")
    assert footprint.contains_zip("56073")  # New Ulm is in
    assert footprint.contains_zip("54016")  # Hudson WI is in
    assert not footprint.contains_zip("55044")  # Lakeville is Spectrum
    assert not footprint.contains_zip("55372")  # Prior Lake is Mediacom
    assert not footprint.contains_zip("")


def test_footprint_matches_city_in_headline(footprint):
    assert footprint.match_city("Northstar Dental to open second clinic in Eagan") == "Eagan"
    assert footprint.match_city("New clinic coming to St. Paul") == "St. Paul"
    assert footprint.match_city("New clinic coming to Saint Paul") == "St. Paul"
    assert footprint.match_city("Maple Grove restaurant expands") == "Maple Grove"
    assert footprint.match_city("Lakeville clinic opens") == ""


def test_city_labels_are_unique_and_nonempty(footprint):
    labels = footprint.city_labels()
    assert len(labels) == len(set(labels))
    assert "Minneapolis" in labels
    assert "Eagan" in labels
