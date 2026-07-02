"""Import eye model geometries to RayOcular."""

from __future__ import annotations

import logging

from pyrot import ro_interface
from pyrot.eye_modelling.datamodels.models import EyeModel

logger = logging.getLogger(__name__)


def import_eye_model(geometry_generators, path_to_json):
    """Updates the eye model of the geometry_generator to match the values of the .json file

    This function gathers patient, case, and examination information from an exported .json file
    (ideally, exported through pyROT's full_export function) and updates an eye model based on this information.

    Parameters
    ----------
    geometry_generators
        The geometry generators object containing the eye model to be updated with the imported data
    path_to_json :
        The path to the .json file containing the eye-model description

    Notes
    -----
    assumes the format of the .json file matches that of the .json files exported by pyROT's full_export function.
    """
    eye_model = EyeModel.load_json(path_to_json)

    new_values = eye_model.parameters.to_rayocular()

    ro_interface.update_eye_model(eye_model_generators=geometry_generators, new_values=new_values)
