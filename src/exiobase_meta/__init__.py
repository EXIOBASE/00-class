from .classifications import ClassificationBundle, read_exio3_classification
from .concordances import read_pi_concordance
from .country_axes import (
	AXIS_NAMES,
	CountryAxis,
	read_all_country_axes,
	read_country_axis,
	read_r12_matrix,
	read_region12,
	region12_codes,
	remind_to_r12,
)
from .country_conversion import convert_countries, convert_country
from .country_names import (
	COCO_NAME_PRE_CONVERT,
	EXIOBASE_OVERRIDES,
	to_exiobase_name,
	to_exiobase_names,
)

__all__ = [
	"AXIS_NAMES",
	"COCO_NAME_PRE_CONVERT",
	"EXIOBASE_OVERRIDES",
	"R12_REGIONS",
	"ClassificationBundle",
	"CountryAxis",
	"convert_countries",
	"convert_country",
	"read_all_country_axes",
	"read_country_axis",
	"read_exio3_classification",
	"read_pi_concordance",
	"read_r12_matrix",
	"read_region12",
	"region12_codes",
	"remind_to_r12",
	"to_exiobase_name",
	"to_exiobase_names",
]


def __getattr__(name: str):
	# Keep ``from exiobase_meta import R12_REGIONS`` working, derived
	# lazily from the bundled region12.csv (never hard-coded).
	if name == "R12_REGIONS":
		from .country_axes import region12_codes as _codes

		return _codes()
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
