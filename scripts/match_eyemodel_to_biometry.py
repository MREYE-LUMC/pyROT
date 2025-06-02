import __common__

import logging

# import sys
from connect import *  # noqa: F403

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling import match_sclera_to_markers, match_with_biometry

# to set logging level in only this script (note that sys needs to be imported for this as well):
# logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)], force=True)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

logger.debug("importing patient data and local variables")

# --- user input
# user input
scleralcenter = (
    "white_to_white_based"  # 'ellipse_fit' (not yet supported), 'axial_length_based' or 'white_to_white_based'
)
rotation_based_on = "optic_disk"  # choose what to base the eye rotation on
poi_type_on = r"LocalizationPoint"

# --- end user input

# get biometry data for current patient (currently relies on center-specific method of loading patient data)
# biometry_data = get_biometry.get_biometry()

# or use standard biometry based on the Navarro eye model/ manually edit this dictionary:
biometry_data = {
    "CCT": 0.55 * 0.1,
    "AD": 3.05 * 0.1,
    "LT": 4.00 * 0.1,
    "AL": 23.92 * 0.1,
    "WTW": 12 * 0.1,  # not from the Navarro eye model
    "AD_offset": 0 * 0.1,
}

logger.debug("used biometry data: %s", biometry_data)


modify_cornea_semi_axis = Config.MODIFY_COR_SEMI_AXIS
marker_location = Config.MARKER_LOCATION
cornea_type = Config.CORNEA_TYPE
roi_name_od = Config.ROI_NAME_OD
roi_name_vitreous = Config.ROI_NAME_VITREOUS

structure_set = ro_interface.load_current_structureset()
eye_model_generators, eye_model_parameters = ro_interface.load_eyemodel(structure_set, Config.EYE_MODEL_NR)

# fit the eye model
logger.debug("start fitting eye model")

# do an full ellipsoid fit on eye model, so we know the vitreous center and length(these are necessary for determine_center_translation_based_on_WTW())
logger.debug("do an full ellipsoid fit, so we know the vitreous center and length")
match_sclera_to_markers.match_sclera_to_markers(
    structure_set, eye_model_generators, eye_model_parameters, "ellipsoid", marker_location
)

# rotate the eye model
match_sclera_to_markers.rotate_eye_model(
    structure_set,
    eye_model_generators,
    eye_model_parameters,
    poi_type_on,
    roi_name_od,
    roi_name_vitreous,
    rotation_based_on,
)

# do the ellipse fit again as the rotation affects the optimal fit
match_sclera_to_markers.match_sclera_to_markers(
    structure_set, eye_model_generators, eye_model_parameters, "ellipsoid", marker_location
)


if scleralcenter == "axial_length_based":
    logger.info("fitting the eye model to the markers and base the scleral center on the axial length")

    # get vitreous length
    sclera_ap_radius = eye_model_parameters.ScleraSemiAxis["y"]
    sclera_inner_ap_radius = (
        sclera_ap_radius - eye_model_parameters.ScleraThickness
    )  # as the sclera AP radius is defined at the outer border of the ROI

    # calculate the posterior shift
    logger.debug("do an ellipsoid fit but fit the center halfway between full ellipsoid fit and AL")
    logger.debug("scleraInnerAPradius: %s", sclera_inner_ap_radius)
    logger.debug("AL: %s", biometry_data["AL"])
    ap_shift = 0.5 * (0.5 * biometry_data["AL"] - sclera_inner_ap_radius)
    logger.debug("APshift : %s", ap_shift)

    # fit the model
    match_sclera_to_markers.match_sclera_to_markers(
        structure_set,
        eye_model_generators,
        eye_model_parameters,
        "ellipsoid_fixedCenter",
        marker_location,
        center_translation=[0, ap_shift, 0],
    )

elif scleralcenter == "white_to_white_based":
    logger.info(
        "fitting the eye model to the markers and place the scleral center so that the sclera width at the iris intersection matches the measured WTW width"
    )

    # determine center location based on the WTW diameter
    logger.debug("determining center translation based on WTW diameter")
    center_translation_based_on_white_to_white = match_sclera_to_markers.calc_sclera_center_to_match_white_to_white(
        structure_set, eye_model_parameters, marker_location, biometry_data
    )

    # fit the model
    logger.debug("fitting the model with a center translation of %s", center_translation_based_on_white_to_white)
    match_sclera_to_markers.match_sclera_to_markers(
        structure_set,
        eye_model_generators,
        eye_model_parameters,
        "ellipsoid_fixedCenter",
        marker_location,
        center_translation=[0, center_translation_based_on_white_to_white, 0],
    )

elif scleralcenter == "ellipse_fit":
    raise NotImplementedError("Unsupported scleralcenter input type")
else:
    raise NotImplementedError(
        'WARNING: script not run. Please input "ellipse_fit", "axial_length_based" or "white_to_white_based" for scleralcenter'
    )

logger.debug("commence setting onaxis distances")
match_with_biometry.match_eye_model(eye_model_generators, eye_model_parameters, biometry_data, cornea_type=cornea_type)
logger.debug("setting onaxis distances completed")
logger.debug("fitting eye model completed")
