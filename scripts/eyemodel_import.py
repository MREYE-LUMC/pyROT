import __common__

import logging
import sys

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling.datamodels import model_import

# to set logging level in only this script (note that sys needs to be imported for this as well):
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)
logger = logging.getLogger(__name__)

logger.debug("commencing import")

patient = ro_interface.load_current_patient()
structure_set = ro_interface.load_current_structureset()
geometry_generators, _ = ro_interface.load_eyemodel(structure_set=structure_set, eyemodelnr=Config.EYE_MODEL_NR)
import_path = Config.IMPORT_PATH  # TODO: iets dat 'eyemodel' dingen die in een .json zitten uit een mapje haalt

model_import.import_eye_model(structure_set, geometry_generators, import_path)


logger.debug("import complete")
