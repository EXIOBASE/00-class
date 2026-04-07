from exiobase_meta import convert_country, read_exio3_classification


def test_read_exio3_classification():
    bundle = read_exio3_classification(with_ranges=True)

    assert "products" in bundle.tables
    assert "industries" in bundle.tables
    assert bundle.ranges is not None
    assert "supply_row" in bundle.ranges


def test_country_conversion():
    assert convert_country("Germany", to="ISO3") == "DEU"
