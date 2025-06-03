"""Fit the sclera ellipsoid to a set of markers."""

from __future__ import annotations

import logging
import math

import numpy as np

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling import common_methods
from pyrot.eye_modelling.ellipsoid_fit import ellipsoid_fit

logger = logging.getLogger(__name__)

logger.debug("Minimum matrix condition set to %s", Config.ELLIPSOID_FIT_MINIMUM_MATRIX_CONDITION)


def match_sclera_to_markers(
    structure_set: object,
    eye_model_generators: object,
    eye_model_parameters: object,
    eye_shape: str,
    marker_location: str,
    center_translation: list | None = None,
) -> None:
    """Fit an ellipsoid to the markers, without using biometry data.

    Parameters
    ----------
    structure_set : object
        The structure set containing the POI geometries.
    eye_model_generators : object
        The eye model containing eye parameters.
    eye_model_parameters : object
        An object with only specific eye model parameters
    eye_shape : str
        The shape of the eye model. Options are "sphere", "EYEPLAN", "ellipsoid", "ellipsoid_fixedCenter".
        "sphere" returns a sphere
        "EYEPLAN" returns an ellipsoid with the same radii in IS and LR directions
        "ellipsoid" returns an ellipsoid
        "ellipsoid_fixedCenter" returns an ellipsoid but uses use a predefined shift in ellipsoid center location
    marker_location : str
        The location of the markers. Options are 'clips', 'choroid', 'nocorrection'.
        "clips" means the location of the clips, which are sutured on the sclera
        "choroid" means the markers are localized on the choroid
        For both "clips" and "choroid", the relevant correction is performed to obtain the sclera radii
    center_translation : list, optional
        The translation of the center, by default [0, 0, 0] (but this is defined in the function as to not use mutable data structures for argument defaults).

    Raises
    ------
    NotImplementedError
        If an unsupported eye shape or marker location is provided.
    """

    logger.debug("start match_sclera_to_markers function")
    logger.debug("eyeShape: %s", eye_shape)
    logger.debug("markerLocation: %s", marker_location)

    if center_translation is None:
        center_translation = [0, 0, 0]

    # Validate input parameters
    if eye_shape not in {"sphere", "EYEPLAN", "ellipsoid", "ellipsoid_fixedCenter"}:
        raise NotImplementedError("Unsupported eye shape")
    if marker_location not in {"clips", "choroid", "nocorrection"}:
        raise NotImplementedError("Unsupported markerLocation type")

    # Note that these transforms are related to DICOM Patient CS
    eye_rotation = eye_model_parameters.EyeRotation
    eye_translation = eye_model_parameters.EyeTranslation
    r_reg = common_methods.getEyeModelToPatientRotationMatrix(eye_rotation["x"], eye_rotation["y"], eye_rotation["z"])
    t_reg = common_methods.getTranslationMatrix(eye_translation["x"], eye_translation["y"], eye_translation["z"])
    matrix_eye_to_patient = t_reg @ r_reg
    matrix_patient_to_eye = np.linalg.inv(matrix_eye_to_patient)

    markers_in_eye = []
    # Get all marker POIs in patient and transform them to eye coordinate system
    poi_geometries = ro_interface.load_pois(structure_set, poi_type=r"Marker")
    for pg in poi_geometries:
        p_patient = np.array([pg.Point["x"], pg.Point["y"], pg.Point["z"], 1.0])  # in the patient coord system
        p_eye = matrix_patient_to_eye @ p_patient  # in the eye coord system
        if np.linalg.norm(center_translation) > 0:  # relative translation to current eye center
            p_eye += np.append(center_translation, [0])  # [0] add as MPtToEye is a 4x4 matrix
        markers_in_eye.append(p_eye[0:3])

    center, radii, evecs, condition_of_inverse = ellipsoid_fit(markers_in_eye, eye_shape)
    # Assert that the eigen vectors are as expected (x,y,z). The algorithm has shown to sometimes generate a different order
    assert abs(np.sum(evecs - np.eye(3))) < 1e-10  # noqa: PLR2004

    assert condition_of_inverse < Config.ELLIPSOID_FIT_MINIMUM_MATRIX_CONDITION, (
        r"Please add an additional marker to make the fit unique"
    )

    if marker_location == "clips":
        # If we assume that the markers are positioned at the center of the clips, we should subtract half clips thickness from the radii
        clip_thick = Config.CLIP_THICKNESS
        radii -= clip_thick / 2
    elif marker_location == "choroid":
        # Assume on the middle of retina/choroid complex is clicked, add half the retina thickness + full sclera thickness
        radii += 0.5 * eye_model_parameters.RetinaThickness + eye_model_parameters.ScleraThickness
    elif marker_location == "nocorrection":
        # Do nothing as the markers are supposedly correctly placed on the sclera
        pass
    else:
        raise NotImplementedError("Unknown parameter value")

    # Transform center position in Eye to Pt CS
    # Apply predefined center translation:
    if np.linalg.norm(center_translation) > 0:  # relative translation to current eye center
        center -= center_translation
    fit_eye_center_patient = matrix_eye_to_patient @ np.append(center, 1)

    # Update eye model
    new_values = {}
    new_values["ScleraSemiAxis"] = [radii[0], radii[1], radii[2]]
    new_values["EyeTranslation"] = [fit_eye_center_patient[0], fit_eye_center_patient[1], fit_eye_center_patient[2]]

    ro_interface.update_eye_model(eye_model_generators, new_values)


def calc_sclera_center_to_match_white_to_white(
    structure_set: object,
    eye_model_parameters: object,
    marker_location: str,
    biometry_data: dict,
    evaluations_start: float = -0.1,
    evaluations_stop: float = 0.2,
    n_evaluations: int = 31,
) -> float:
    """Calculate the ellipsoid center location so it matches the WTW-width at vitreous depth.
    This is to ensure the models limbus diameter matches the measured limbus diameter/ White To White,
    without compromising on correctness of anterior chamber biometry.

    Uses linear interpolation to find this center translation.
    By default calculates one sample per .1 mm to account for the nonlinearity of the limbus diameter and center translation relation.
    Using less samples with a quadratic interpolation using e.g. scipy would be more efficient/ elegant, but this is not possible in some (clinical) RayOcular scripting environments.

    Parameters
    ----------
    structure_set : object
        The structure set containing the POI geometries.
    eye_model_parameters : object
        An object containing only specific eye model parameters
    marker_location : str
        The location of the markers. Options are 'clips', 'choroid', 'nocorrection'.
    biometry_data : dict
        The biometry data containing measurements like 'AL', 'AD', 'AD_offset', and 'WTW'.
    evaluations_start : float
        The minimal center translation to be evaluated in cm, by default -.1
    evaluations_stop : float
        The maximal center translation to be evaluated in cm, by default .2
    n_evaluations : int, optional
        The number of evaluations for center translations, by default 31.

    Returns
    -------
    float
        The center translation based on the WTW radius.

    Raises
    ------
    LookupError
        If the WTW radius is outside the range of evaluated limbus half-axes.
        This would mean the limbus diameter of the model would differ from the measured limbus diameter
    """

    logger.debug("start calc_sclera_center_to_match_white_to_white function")
    # Define a list of center translations to evaluate (best fitting ellipse center+translation = 0 )
    center_translations = np.linspace(start=evaluations_start, stop=evaluations_stop, num=n_evaluations)

    # Find the sclera ellipse radii for each center translation
    radii_list = calc_sclera_ellipse_for_center(
        structure_set, eye_model_parameters, marker_location, center_translations=center_translations
    )

    # Find the limbus half-axis for each set of sclera radii
    limbus_halfaxes = calc_limbusrad(eye_model_parameters, biometry_data, radii_list)

    logger.debug("Center translations evaluated: %s", center_translations)
    logger.debug("Corresponding radii: %s", radii_list)
    logger.debug("Limbus half-axes: %s", limbus_halfaxes)

    # The range of necessary evaluated center translations differs much per patient
    # On the one hand, we want to evaluated a fixed amount of center translatiosn for each patient
    # On the other hand, this prompts us to evaluate some very extreme center translations in some patients, leading to extreme values
    # these extreme eye models can be recognised by seeing that a larger center translation to posterior leads to a larger limbus radius
    # these extreme eye models would clutter the linear interpolation, so we detect and delete these evaluated eye models and give the user a warning if this happens

    min_limbus_halfaxis = np.min(limbus_halfaxes)
    if min_limbus_halfaxis != limbus_halfaxes[0]:
        loc_min_limbus_halfaxis = list(limbus_halfaxes).index(min_limbus_halfaxis)
        limbus_halfaxes = limbus_halfaxes[loc_min_limbus_halfaxis:]  # delete the extreme eye models
        center_translations = center_translations[loc_min_limbus_halfaxis:]
        logger.info(
            "Some unrealistic limbus models were found, these are deleted.\nInput for linear interpolation are:\n center_translations: %s and limbus_halfaxes: %s",
            center_translations,
            limbus_halfaxes,
        )

    # Find the center translation necessary for the known limbus half_axis
    white_to_white_radius = 0.5 * biometry_data["WTW"]  # as it is the semi-axis

    # Check if the WTW radius is within the range of evaluated limbus half-axes
    if white_to_white_radius > limbus_halfaxes[-1]:
        logger.warning("inputted limbus half-axis is larger than largest evaluated limbus half-axes")
    if white_to_white_radius < limbus_halfaxes[0]:  # we just made sure the first value is the smallest value
        logger.warning("inputted limbus half-axis is smaller than smallest evaluated limbus half-axes")

    # use linear interpolation to find the necessary center translation
    center_translation_based_on_white_to_white = np.interp(
        x=white_to_white_radius, xp=limbus_halfaxes, fp=center_translations
    )

    logger.debug(
        "Limbus white_to_white_radius of %s corresponds to a center_translation_based_on_WTW of %s",
        white_to_white_radius,
        center_translation_based_on_white_to_white,
    )

    return center_translation_based_on_white_to_white


def calc_sclera_ellipse_for_center(
    structure_set: object, eye_model_parameters: object, marker_location: str, center_translations: list
) -> list:
    """Returns best fitting sclera ellipse radii to marker locations for one or an array of ellipse center locations.

    Parameters
    ----------
    structure_set : object
        The structure set containing the POI geometries.
    eye_model_parameters : object
        The eye model object containing only eye parameters
    marker_location : str
        The location of the markers. Options are 'clips', 'choroid', 'nocorrection'.
    center_translations : list
        The center translations to evaluate.

    Returns
    -------
    list
        List of radii for each center translation.

    Raises
    ------
    NotImplementedError
        If an unsupported marker location is provided.
    """

    # TODO: future: merge with fit_eye_model_to_markers

    logger.debug("start calc_sclera_ellipse_for_center function")

    # Validate input parameters
    if marker_location not in {"clips", "choroid", "nocorrection"}:
        raise NotImplementedError("Unsupported markerLocation type")
    center_translations_array = np.atleast_1d(center_translations)

    # Note that these transforms are related to DICOM Patient CS
    eye_rotation = eye_model_parameters.EyeRotation
    eye_translation = eye_model_parameters.EyeTranslation
    r_reg = common_methods.getEyeModelToPatientRotationMatrix(eye_rotation["x"], eye_rotation["y"], eye_rotation["z"])
    t_reg = common_methods.getTranslationMatrix(eye_translation["x"], eye_translation["y"], eye_translation["z"])
    matrix_eye_to_patient = t_reg @ r_reg
    matrix_patient_to_eye = np.linalg.inv(matrix_eye_to_patient)

    markers_in_eye = []
    # Get all marker POIs in patient and transform them to eye coordinate
    poi_geometries = ro_interface.load_pois(structure_set, poi_type=r"Marker")
    for pg in poi_geometries:
        p_patient = np.array([pg.Point["x"], pg.Point["y"], pg.Point["z"], 1.0])  # in the patient coord system
        p_eye = matrix_patient_to_eye @ p_patient  # in the eye coord system
        markers_in_eye.append(p_eye[0:3])

    # Find radii for each center translation
    radii_list = []
    for center_translation in center_translations_array:
        # Shift all marker POIs by one center translation
        markers_for_fit = np.array(markers_in_eye.copy())
        markers_for_fit[:, 1] += center_translation

        # Fit the corresponding center, radii and evecs
        center, radii, evecs, condition_of_inverse = ellipsoid_fit(markers_for_fit, eye_shape="ellipsoid_fixedCenter")

        # Assert that the eigen vectors are as expected (x, y, z). The algorithm has shown to sometimes generate a different order
        assert abs(np.sum(evecs - np.eye(3))) < 1e-10  # noqa: PLR2004

        assert condition_of_inverse < Config.ELLIPSOID_FIT_MINIMUM_MATRIX_CONDITION, (
            r"Please add an additional marker to make the fit unique"
        )

        # Calculate sclera ellipse radii from the radii of the ellipse fitted through the input POIs
        if marker_location == "clips":
            # If we assume that the markers are positioned at the center of the clips, we should subtract
            # half clips thickness from the radii
            clip_thick = Config.CLIP_THICKNESS
            radii -= clip_thick / 2
        elif marker_location == "choroid":
            # Assume on the middle of retina/choroid complex is clicked, add half the retina thickness + full sclera thickness
            radii += 0.5 * eye_model_parameters.RetinaThickness + eye_model_parameters.ScleraThickness
        elif marker_location == "nocorrection":
            # Do nothing as they are supposedly correctly placed
            pass
        else:
            raise NotImplementedError("Unknown parameter value")

        radii_list.append(radii)

    if len(center_translations) == 1:  # Only one offset is supplied
        return radii_list[0]

    return radii_list


def calc_limbusrad(eye_model_parameters: object, biometry_data: dict, radii_list: list) -> float or list:
    """Determines limbus half-axes of one or an array of sclera ellipses so it matches the vitreous depth.

    Parameters
    ----------
    eye_model_parameters : object
        An object containing only specific eye parameters
    biometry_data : dict
        The biometry data containing measurements like 'AL', 'AD', and 'AD_offset'.
    radii_list : list
        List of radii for each center translation.

    Returns
    -------
    float or list
        The limbus half-axes for the given sclera ellipses.
    """

    logger.debug("start calc_limbusrad function")

    # Validate input parameters
    radii_list_2d = np.atleast_2d(radii_list)

    # Get relevant biometry
    sclera_lr_outer_radii = radii_list_2d[:, 0]
    sclera_is_outer_radii = radii_list_2d[:, 2]
    sclera_ap_outer_radii = radii_list_2d[:, 1]
    sclera_thickness = eye_model_parameters.ScleraThickness
    iris_thickness = eye_model_parameters.IrisThickness
    retina_thickness = eye_model_parameters.RetinaThickness

    # Convert relevant biometry measurements
    cornea_thickness = biometry_data["CCT"]
    aqueous_depth = biometry_data["AD"] + biometry_data["AD_offset"]
    vitreous_depth_incl_lens = biometry_data["AL"] - aqueous_depth - cornea_thickness

    # Determine the limbus diameter for these sclera diameters and biometry
    sclera_min_outer_radii = np.minimum(sclera_lr_outer_radii, sclera_is_outer_radii)
    sclera_min_innerradii = sclera_min_outer_radii - sclera_thickness
    sclera_ap_innerradii = sclera_ap_outer_radii - sclera_thickness

    # As the posterior half of the vitreous is already included, we only need the front part
    # Additionally, include the intersection defined at half the iris thickness
    vitr_incl_lens_retina_and_half_iris = vitreous_depth_incl_lens + 0.5 * iris_thickness + retina_thickness
    effective_depths = vitr_incl_lens_retina_and_half_iris - sclera_ap_innerradii

    # Find the corresponding limbus half-axes
    # (and set this to 0 in extreme eye models where the limbus is situated anterior to the sclera ellipse,
    #  which would result in the sqrt of an negative number)

    limbus_half_axes = sclera_min_innerradii * np.sqrt(
        np.maximum(1 - (effective_depths**2) / (sclera_ap_innerradii**2), 0)
    )

    if len(radii_list) == 1:
        return limbus_half_axes[0].item()

    return limbus_half_axes


# Start methods that are used to rotate the eye to match the optic nerve


def rotate_eye_model(
    structure_set: object,
    eye_model_generators: object,
    eye_model_parameters: object,
    poi_type_on: str,
    roi_name_od: str,
    roi_name_vitreous: str,
    based_on: str = "optic_disk",
):
    """Rotates the eye model automatically, based on user input.

    Parameters
    ----------
    structure_set : object
        The structure set containing the POI geometries.
    eye_model_generators : object
        The eye model containing eye parameters.
    eye_model_parameters : object
        An object containing specific eye parameters
    poi_type_on : str
        The poi type the poi that defines the optic nerve/disk location is designated by
        It is necessary that there is only one poi of this type
    based_on : str
        What the rotation will be based on. Currently, only 'optic_disk' is supported
    roi_name_od : str
        The name of the ROI of the optic disk in the eye model

    Raises
    ------
    NotImplementedError
        If the method designated in the 'based_on' variable is not supported
    """

    logger.debug("start rotate_eye_model function")

    if based_on == "optic_disk":
        # import the location of the optic disk
        on_image_loc = ro_interface.load_pois(structure_set, poi_type=poi_type_on)
        # assert that there is only one poi with this poi type
        if len(on_image_loc) != 1:
            raise ValueError(f"multiple pois of the type {poi_type_on} exist")
        on_image_loc = on_image_loc[0]

        # import the eyes current rotation
        eye_rotation_in = eye_model_parameters.EyeRotation
        # import all rois
        rois = ro_interface.load_rois(structure_set)

        # set input for rotation functions
        # use the center of the vitreous as a proxy for the center of the retina ellipse
        retina_center_rl = rois[roi_name_vitreous].GetCenterOfRoi()["x"]
        retina_center_ap = rois[roi_name_vitreous].GetCenterOfRoi()["y"]
        retina_center_is = rois[roi_name_vitreous].GetCenterOfRoi()["z"]

        # the sclera semi axis is defined on the outside of the sclera while the center of the optic disk ROI is approximately in the middle of the retina
        retina_axis_rl = (
            eye_model_parameters.ScleraSemiAxis["x"]
            - eye_model_parameters.ScleraThickness
            - 0.5 * eye_model_parameters.RetinaThickness
        )
        retina_axis_ap = (
            eye_model_parameters.ScleraSemiAxis["y"]
            - eye_model_parameters.ScleraThickness
            - 0.5 * eye_model_parameters.RetinaThickness
        )
        retina_axis_is = (
            eye_model_parameters.ScleraSemiAxis["z"]
            - eye_model_parameters.ScleraThickness
            - 0.5 * eye_model_parameters.RetinaThickness
        )

        optic_disc_eyemodel_rl = rois[roi_name_od].GetCenterOfRoi()["x"]
        optic_disc_eyemodel_ap = rois[roi_name_od].GetCenterOfRoi()["y"]
        optic_disc_eyemodel_is = rois[roi_name_od].GetCenterOfRoi()["z"]

        optic_disc_poi_rl = on_image_loc.Point["x"]
        optic_disc_poi_ap = on_image_loc.Point["y"]
        optic_disc_poi_is = on_image_loc.Point["z"]

        # calculate the roll difference between the current location of the optic disk and the clicked poi
        roll_angle_deg = calc_rotation_to_align_points(
            retina_center=(retina_center_rl, retina_center_ap),
            retina_axes=(retina_axis_rl, retina_axis_ap),
            optic_disc_eyemodel=(optic_disc_eyemodel_rl, optic_disc_eyemodel_ap),
            optic_disc_poi=(optic_disc_poi_rl, optic_disc_poi_ap),
        )

        # calculate the pitch difference between the current location of the optic disk and the clicked poi
        pitch_angle_deg = calc_rotation_to_align_points(
            retina_center=(retina_center_ap, retina_center_is),
            retina_axes=(retina_axis_ap, retina_axis_is),
            optic_disc_eyemodel=(optic_disc_eyemodel_ap, optic_disc_eyemodel_is),
            optic_disc_poi=(optic_disc_poi_ap, optic_disc_poi_is),
        )

        # input in model, keeping in mind that the model already had a rotation before our calculations
        new_values = {}
        new_values["EyeRotation"] = np.asarray(
            [eye_rotation_in["x"] + pitch_angle_deg, eye_rotation_in["y"], eye_rotation_in["z"] + roll_angle_deg]
        )

        ro_interface.update_eye_model(eye_model_generators, new_values)

    else:
        raise NotImplementedError(f"This method: {based_on} is not implemented")


def project_point_to_ellipse(center, axes, point):
    """Projects a point onto the boundary of an ellipse.

    Does this by first calculating the function of the line between the point and the center of the sclera.
    Subsequently, the intersection between this line and the sclera ellipse is calculated.

    Parameters
    ----------
    center (tuple)
        (x_c, y_c) center of the ellipse.
    axes (tuple)
        (a, b) ellipse semi-axes.
    point (tuple)
        (x, y) coordinates of the point to project.

    Returns
    -------
        tuple: (x_proj, y_proj) coordinates of the projected point on the ellipse.
    """

    logger.debug("start project_point_to_ellipse function")

    x_c, y_c = center
    a, b = axes
    x, y = point

    # Translate point to ellipse-centered coordinates. This gives us a vector.
    x_prime = x - x_c
    y_prime = y - y_c

    if x_prime == 0 and y_prime == 0:
        raise ValueError("Point is at the ellipse center; projection is undefined.")

    # Compute scaling factor. This scaling factor is the size to which we need to scale the vector so it intersects with the ellipse
    scale = 1 / np.sqrt((x_prime**2 / a**2) + (y_prime**2 / b**2))

    # Projected coordinates (center location plus the vector multiplied by the scale)
    x_proj = x_c + scale * x_prime
    y_proj = y_c + scale * y_prime

    return x_proj, y_proj


def calc_angle_between_points(center, from_point, to_point):
    """Computes the angle (in degrees) needed to rotate from one point to another, relative to the same center.

    Parameters
    ----------
    center (tuple)
        (x_c, y_c) center of rotation.
    from_point (tuple)
        (x1, y1) starting point.
    to_point (tuple)
        (x2, y2) target point.

    Returns
    -------
    float : Rotation angle in degrees (positive = counter-clockwise).
    """

    logger.debug("start calc_angle_between_points function")

    x_c, y_c = center
    x1, y1 = from_point
    x2, y2 = to_point

    angle_from = math.atan2(
        y1 - y_c, x1 - x_c
    )  # the angle between the most posterior point of the ellipse and the first point
    angle_to = math.atan2(
        y2 - y_c, x2 - x_c
    )  # the angle between the most posterior point of the ellipse and the second point
    angle_rad = angle_to - angle_from  # the angle between both points on the ellipse

    return math.degrees(angle_rad)


def calc_rotation_to_align_points(
    retina_center: tuple,
    retina_axes: tuple,
    optic_disc_eyemodel: tuple,
    optic_disc_poi: tuple,
) -> float:
    """Main wrapper function to compute the optimal rotation angle (in degrees)
    to align an ellipse_point with the projection of a manual_input.

    Parameters
    ----------
    retina_center (tuple)
        (x_c, y_c) center of the ellipse.
    retina_axes (tuple)
        (a, b) retina ellipse axes.
    optic_disc_eyemodel (tuple)
        the location of the optic disk of the current eye model
    optic_disc_poi (tuple)
        the clicked poi of the actual location of the optic disk

    Returns
    -------
    float : Rotation angle in degrees.
    """

    logger.debug("start calc_rotation_to_align_points function")

    # Project the input onto the retina ellipse
    optic_disc_poi_on_ellipse = project_point_to_ellipse(retina_center, retina_axes, optic_disc_poi)
    optic_disc_eyemodel_on_ellipse = project_point_to_ellipse(retina_center, retina_axes, optic_disc_eyemodel)

    # Compute the rotation angle from the optic disk of the eye model (projected to the sclera) to the input optic disc location poi (projected to the sclera)
    return calc_angle_between_points(retina_center, optic_disc_eyemodel_on_ellipse, optic_disc_poi_on_ellipse)


# End methods that are used to rotate the eye to match the optic nerve
