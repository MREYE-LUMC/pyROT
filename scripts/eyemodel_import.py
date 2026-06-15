import __common__

import logging
import os
import sys

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling.datamodels import model_import

# to set logging level in only this script (note that sys needs to be imported for this as well):
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)
logger = logging.getLogger(__name__)

logger.debug("commencing import")

patient = ro_interface.load_current_patient()
import_directory = Config.IMPORT_DIRECTORY
import_file_name_element = Config.IMPORT_FILE_NAME_ELEMENT
eye_model_files = [file for file in os.listdir(import_directory) if import_file_name_element in file]
if len(eye_model_files) != 1:
    raise KeyError(
        f"import directory {import_directory} contains {len(eye_model_files)} files where only one is expected, please alter Config.IMPORT_FILE_NAME_ELEMENT in customization.py"
    )
import_path = os.path.join(import_directory, eye_model_files[0])

structure_set = ro_interface.load_current_structureset()
geometry_generators, _ = ro_interface.load_eyemodel(structure_set=structure_set, eyemodelnr=Config.EYE_MODEL_NR)

# import the eye model to the relevant structure_set and geometry_generators object
model_import.import_eye_model(geometry_generators, import_path)


logger.debug("import complete")
