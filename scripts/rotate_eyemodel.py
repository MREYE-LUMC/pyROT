import __common__

import logging
import sys

from connect import *  # noqa: F403

import pyrot.eye_modelling.match_sclera_to_markers as rotate_eyemodel
from pyrot import ro_interface
from pyrot.config import Config

# to set logging level in only this script (note that sys needs to be imported for this as well):
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)
logger = logging.getLogger(__name__)

logger.debug("importing patient data and local varialbes")

# user input
based_on = "optic_disk"  # choose what to base the eye rotation on
poi_type_on = r"LocalizationPoint"

###
eyemodelnr = Config.EYE_MODEL_NR
structure_set = ro_interface.load_current_structureset()
eye_model_generators, eye_model_parameters = ro_interface.load_eyemodel(structure_set, eyemodelnr)
roi_name_od = Config.ROI_NAME_OD
roi_name_vitreous = Config.ROI_NAME_VITREOUS

logger.debug("commence rotating eye model")
rotate_eyemodel.rotate_eye_model(
    structure_set,
    eye_model_generators,
    eye_model_parameters,
    poi_type_on,
    roi_name_od=roi_name_od,
    roi_name_vitreous=roi_name_vitreous,
    based_on=based_on,
)

logger.debug("rotating eye model completed")
