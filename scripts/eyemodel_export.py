import __common__

import logging
import sys

from pyrot.config import Config
from pyrot.eye_modelling.datamodels import export

# to set logging level in only this script (note that sys needs to be imported for this as well):
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)
logger = logging.getLogger(__name__)

logger.debug("commencing export")

export.full_export(
    output_directory=Config.EXPORT_OUTPUT_DATA_PATH,
    eyemodelnr=Config.EYE_MODEL_NR,
    export_suffix=Config.ROI_EXPORT_ROI_SUFFIX,
    roi_export_unit=Config.ROI_EXPORT_UNIT,
)

logger.debug("export complete")
