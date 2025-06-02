from __future__ import annotations

import __common__

import logging
import sys
from typing import Optional

from pyrot import ro_interface
from pyrot.config import Config

logger = logging.getLogger(__name__)


datapath = Config.PAT_DATA_PATH
sys.path.insert(1, datapath)
import pats  # noqa: E402


def get_biometry(patid: Optional[str] = None):
    # gets the biometry data from a .py file in which the patient data is stored.
    # if no patid is specified, finds the patid in the patient name in RayOcular
    if patid is None:
        patient = ro_interface.load_current_patient()
        pat_id_ro = patient.PatientID
        patid = f"{Config.NAME_PREFIX}{pat_id_ro.split(Config.NAME_PREFIX)[1]}"
        logger.debug("no patid specified, proceeding with %s", patid)

    return pats.pats[patid]
