import exiobase_meta as em
from exiobase_meta import (
    convert_country,
    read_exio3_classification,
    read_pi_concordance,
    read_region12,
    region12_codes,
    remind_to_r12,
)


def test_pi_concordance_shape_and_binary():
    # Product-to-industry concordance is shipped as package data and read
    # here, not from a hardcoded class/ path. 200 products x 163 industries,
    # binary, each product maps to exactly one industry (row sums to 1).
    df = read_pi_concordance()
    assert df.shape == (200, 163)
    assert df.index.name == "product"
    assert df.columns.name == "industry"
    assert set(df.to_numpy().ravel().tolist()) <= {0.0, 1.0}
    assert (df.sum(axis=1) == 1).all()


def test_region12_is_csv_driven():
    df = read_region12()
    # The 12-region grouping comes from data/class/region12.csv, not code.
    assert list(df.columns) == ["region12", "name", "remind_source"]
    assert len(df) == 12
    # The backward-compat constant is derived from the CSV, in file order.
    assert em.R12_REGIONS == region12_codes() == tuple(df["region12"])


def test_region12_relabels_from_csv():
    # The EXIOBASE relabels of country_converter's REMIND codes live in the
    # CSV's remind_source column, not a hard-coded dict.
    relabel = remind_to_r12()
    assert relabel["CAZ"] == "CAU"
    assert relabel["REF"] == "RUS"
    # The other ten REMIND codes map to themselves.
    assert sum(1 for k, v in relabel.items() if k != v) == 2


def test_read_exio3_classification():
    bundle = read_exio3_classification(with_ranges=True)

    assert "products" in bundle.tables
    assert "industries" in bundle.tables
    assert bundle.ranges is not None
    assert "supply_row" in bundle.ranges


def test_country_conversion():
    assert convert_country("Germany", to="ISO3") == "DEU"
