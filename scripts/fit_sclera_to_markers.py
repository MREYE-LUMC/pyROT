from __future__ import annotations

import __common__

import logging
import sys

import numpy as np
from connect import *  # noqa: F403

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling import match_sclera_to_markers

# to set logging level in only this script (note that sys needs to be imported for this as well):
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)

logger = logging.getLogger(__name__)

logger.debug("importing patient data and local variables")

eyemodelnr = Config.EYE_MODEL_NR

structure_set = ro_interface.load_current_structureset()
eye_model_generators, eye_model_parameters = ro_interface.load_eyemodel(structure_set, eyemodelnr)

# eye_shape = r"sphere"
# eye_shape = r"EYEPLAN" # same radii in LR and FH directions
eye_shape = r"ellipsoid"  # fit radii in all 3 directions (but no rotations of the eigenvectors)
# eye_shape = r"ellipsoid_fixedCenter" # fit radii in all 3 directions and use a predefined shift in ellipsoid center

marker_location = Config.MARKER_LOCATION

center_translation = np.array([0, 0.3, 0]) if eye_shape == "ellipsoid_fixedCenter" else np.array([0, 0, 0])

logger.debug("commencing matching the sclera to the markers")
match_sclera_to_markers.match_sclera_to_markers(
    structure_set, eye_model_generators, eye_model_parameters, eye_shape, marker_location, center_translation
)
logger.debug("matching complete")
