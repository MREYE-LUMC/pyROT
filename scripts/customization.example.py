"""Site-specific customizations for pyROT.

This example file demonstrates how to customize pyROT's behaviour.
To use this file, rename it to `customization.py` and modify the contents as needed.
If present, customization.py will be loaded by __common__.py at the beginning of each script.

Setting config variables in customization.py will override them for all scripts.
To override a specific config variable for a single script, set it in the script itself.
"""

from pyrot.config import Config

# Set the ellipsoid fit to consider matrix inversions with a condition lower than 50 as ill-conditioned.
Config.ELLIPSOID_FIT_MINIMUM_MATRIX_CONDITION = 50

# Add another configuration variable to the Config object.
# Note that this configuration variable is not used by pyROT, but you can use it in your own scripts.
Config.CUSTOM_CONFIG_VARIABLE = 42

# Set the location of the patient data
Config.PAT_DATA_PATH = r"\\path\to\data"

# Set the location where exports should be exported to
Config.EXPORT_OUTPUT_DATA_PATH = r"\\path\to\data"

# Set the prefix that is specific to the study name of the patient
Config.NAME_PREFIX = "STUDY_ABBREVIATION"
