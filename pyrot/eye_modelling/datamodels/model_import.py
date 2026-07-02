"""Import eye model geometries to RayOcular."""

from __future__ import annotations

import logging

from pyrot import ro_interface
from pyrot.eye_modelling.datamodels.models import EyeModel

logger = logging.getLogger(__name__)


def import_eye_model(geometry_generators, import_path):
    """Import all relevant data to a given eye model from a structured output directory.

    This function gathers patient, case, and examination information from an exported .json file
    (ideally, exported through pyROT's full_export function) and updates an eye model based on this information.

    Parameters
    ----------
    geometry_generators
        The geometry generators object containing the eye model to be updated with the imported data
    import_path :
        The path to the .json file containing the eye-model description

    Notes
    -----
    assumes the format of the .json file matches that of the .json files exported by pyROT's full_export function.
    """
    eye_model = EyeModel.load_json(import_path)

    new_values = eye_model.parameters.to_rayocular()

    ro_interface.update_eye_model(eye_model_generators=geometry_generators, new_values=new_values)
