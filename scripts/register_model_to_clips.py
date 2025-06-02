import __common__

import logging
import sys

from connect import *  # noqa: F403

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling import clipbased_model

# to set logging level in only this script (note that sys needs to be imported for this as well):
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)
logger = logging.getLogger(__name__)

logger.debug("importing patient data and local variables")

eyemodelnr = Config.EYE_MODEL_NR

# user input

input_ellipse = "sclera_radii"
poi_type_clips = r"Registration"
poi_type_on = r"LocalizationPoint"

###

structure_set = ro_interface.load_current_structureset()
eye_model_generators, eye_model_parameters = ro_interface.load_eyemodel(structure_set, eyemodelnr)

logger.debug("commencing clip based model fit")
clipbased_model.match_ellipse_with_pois(
    eye_model_generators, eye_model_parameters, structure_set, input_ellipse, poi_type_clips, poi_type_on
)
logger.debug("clip based model fit completed")
