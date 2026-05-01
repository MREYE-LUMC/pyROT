"""Import eye model geometries to RayOcular."""

# TODO:  walk through imports, assumed these should more ore less be equal to those of export.py

from __future__ import annotations

import logging

from pyrot import ro_interface
from pyrot.eye_modelling.datamodels.models import EyeModel

logger = logging.getLogger(__name__)


def import_eye_model(structure_set, geometry_generators, import_path):

    eye_model = EyeModel.load_json(import_path)

    new_values = eye_model.parameters.to_rayocular()

    print(new_values)


    ro_interface.update_eye_model(eye_model_generators=geometry_generators, new_values=new_values)


    # TODO: lenscorneadistance en levelofdetail moeten nog in een list gezet worden (nu handmatig)
    # TODO: oogmodel parameters van chamber en vitreous body moeten eruit gehaald (nu handmatig)
    # TODO: testen of hier hetzelfde oogmodel weer uit komt
    # TODO: kijken of de rotaties (en voor de zekerheid de afmetingen) in xyz ook echt in die volgorde moeten worden ingeladen
    # TODO: .json bestand pad uit uitgebreider mappen-directory halen


    print(new_values)
    print(eye_model.parameters.sclera.semi_axis)
