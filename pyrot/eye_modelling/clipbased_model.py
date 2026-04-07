"""Clip-based registration of the eye model to image and marker data.

This module provides functions to register an eye model to
scleral clip positions and optic nerve/disk-related points of interest.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from pyrot import ro_interface
from pyrot.config import Config
from pyrot.eye_modelling import match_sclera_to_markers

logger = logging.getLogger(__name__)


def match_ellipse_with_pois(
    eye_model_generators,
    eye_model_parameters,
    structure_set,
    input_ellipse,
    poi_type_clips,
    poi_type_on,
    rotation_method,
):
    """Registers the eye model to to the clip locations (on the sclera) and optic disk location.
    Rotation of the eye model is either determined by minimizing the distance to the optic disk POI, or by rotating the
    model such that the visual axis goes through the eye center and optic disk POI.
    In the first case the eye center and rotation are fit parameters, while in  latter case the eye center is the only
    fitting parameter.

    Parameters
    ----------
    eye_model_generators : object
        The eye model containing eye parameters
    eye_model_parameters : object
        Object containing specific parameters of the eye model, such as translation and rotation.
    structure_set : object
        Data structure containing the set of structures (e.g., ROIs, POIs) for the eye model.
    input_ellipse : str
        Specifies which ellipse radii to use for fitting (e.g., "sclera_radii").
    poi_type_clips : str
        The type of POIs representing the clip locations on the sclera.
    poi_type_on : str
        The type of POI representing the optic disk location.
    rotation_method : str
        Method to determine rotation, either "minimize_distance" (fit rotation to minimize optic disk poi - optic disk center distance) or "fixed_gaze" (calculate rotation based on the location of the optic disk POI).

    Raises
    ------
    ValueError
        If there are multiple or no POIs of the specified optic disk type.
    NotImplementedError
        If the specified input_ellipse or rotation_method is not implemented.

    Notes
    -----
    This function updates the eye model parameters (translation, rotation) in-place
    """
    logger.debug("Starting match_ellipse_with_pois function")

    # determinations/ imports that are universal between rotation methods

    eye_translation = eye_model_parameters.EyeTranslation
    eye_translation_input = [eye_translation["x"], eye_translation["y"], eye_translation["z"]]

    # get marker locations
    poi_geometries = ro_interface.load_pois(structure_set, poi_type=poi_type_clips)
    markers_in_patient = [np.array([pg.Point["x"], pg.Point["y"], pg.Point["z"]]) for pg in poi_geometries]

    # find the POI clicked at the location of the OD on the MRI-image.
    # make sure there is exactly one of the designated POI type
    on_image_loc_list = ro_interface.load_pois(structure_set, poi_type=poi_type_on)
    if len(on_image_loc_list) != 1:
        raise ValueError(f"ERROR: multiple or no POIs of type {poi_type_on} exist")
    on_image_loc = on_image_loc_list[0]
    on_image_loc_patient = np.array([on_image_loc.Point["x"], on_image_loc.Point["y"], on_image_loc.Point["z"]])

    # radii of the ellipse to be fitted to the POI's
    if input_ellipse == "sclera_radii":
        sclera_radii = eye_model_parameters.ScleraSemiAxis
        # note that the pois are clicked at the center of the clips, which means we should add 0.5 * clip_thickness to obtain the effective sclera radii at the POI locations
        clip_thickness = Config.CLIP_THICKNESS
        axes = (
            sclera_radii["x"] + (0.5 * clip_thickness),
            sclera_radii["y"] + (0.5 * clip_thickness),
            sclera_radii["z"] + (0.5 * clip_thickness),
        )
    else:
        raise NotImplementedError(f"input_ellipse {input_ellipse} not implemented")

    # determinations/ imports that are specific to one rotation method

    # get the location of the optic nerve in the model, either by getting the location on the unity circle (if rotation_method == fit) or the actual location (if rotation_method == calculate)
    if rotation_method == "minimize_distance":
        on_model_loc_patient = calc_on_model_loc_patient(
            eye_model_generators, eye_model_parameters, "unity_circle_standard_model"
        )
    elif rotation_method == "fixed_gaze":
        # get the current rotation of the eye model
        eye_rotation_in = eye_model_parameters.EyeRotation

        # get the location of the optic nerve in the eye model
        on_model = ro_interface.load_rois(structure_set, roi_name_contains=Config.ROI_NAME_OD)

        # the item that comes from load_rois is a list, get the first item on that list (and give a warning if the list has length >1)
        if len(on_model) > 1:
            logger.warning("Multiple optic disk ROIs found, taking the first one")

        on_model = on_model[0]

        on_model_center = on_model.GetCenterOfRoi()
        on_model_loc_patient = np.array([on_model_center["x"], on_model_center["y"], on_model_center["z"]])

        # get the location of the center of the vitreous body (thus of the sclera) in the eye model
        vitreous_model = ro_interface.load_rois(structure_set, roi_name_contains=Config.ROI_NAME_VITREOUS)

        # the item that comes from load_rois is a list, get the first item on that list (and give a warning if the list has length >1)
        if len(vitreous_model) > 1:
            logger.warning("Multiple vitreous body ROIs found, taking the first one")

        vitreous_model = vitreous_model[0]

        vitreous_model_center = vitreous_model.GetCenterOfRoi()
        vitreous_model_loc_patient = np.array(
            [vitreous_model_center["x"], vitreous_model_center["y"], vitreous_model_center["z"]]
        )
    else:
        raise NotImplementedError(f'rotation_method "{rotation_method}" is not implemented')

    # determine the translation and rotation with the given method
    if rotation_method == "minimize_distance":
        # fit the best location for the ellipsoid to minimize distance from POIs, setting rotation input to 0
        eye_translation_output, eye_rotation_output = calc_ellipsoid_registration_with_fitted_rotation(
            markers_in_patient,
            on_model_loc_patient,
            on_image_loc_patient,
            axes,
            initial_guess=[*eye_translation_input, 0, 0, 0],
        )

        # determine dict to update eye model
        new_values = {}
        new_values["EyeTranslation"] = eye_translation_output
        new_values["EyeRotation"] = eye_rotation_output

    elif rotation_method == "fixed_gaze":
        # fit the best location for the ellipsoid to minimize distance from POIs, and base rotation on the optic disk poi
        eye_translation_output = calc_ellipsoid_registration_with_calculated_rotation(
            markers_in_patient,
            on_model_loc_patient,
            on_image_loc_patient,
            axes,
            vitreous_model_loc_patient,
            eye_rotation_in,
            eye_translation_input,
            initial_guess=eye_translation_input,
        )

        # calculate the corresponding rotation (this is also calculated in the residuals function but is exported)
        roll_angle_deg, pitch_angle_deg = calc_roll_and_pitch_of_shifted_eyemodel(
            vitreous_model_loc_patient,
            axes,
            on_model_loc_patient,
            on_image_loc_patient,
            eye_translation_input,
            eye_translation_output,
        )

        # determine dict to update eye model
        new_values = {}
        new_values["EyeTranslation"] = eye_translation_output
        new_values["EyeRotation"] = np.asarray(
            [eye_rotation_in["x"] + pitch_angle_deg, eye_rotation_in["y"], eye_rotation_in["z"] + roll_angle_deg]
        )

    # update eye model
    logger.debug("updating eyemodel with new eye model values %s:", new_values)
    eye_model_generators.EyeModelParameters.EditEyeModelParameters(NewValues=new_values)


def calc_on_model_loc_patient(geometry_generators, eye_model_parameters, on_model_loc_method):
    """Determines the location of the optic disk as if the eye model were positioned at the origin
    ([0, 0, 0]) with input angles [0, 0, 0] and sclera radii of [1, 1, 1]. This is necessary as the method where
    rotation is fitted, relies on a methodology where all pois are translated to the unity circle.
    Currently, only the "unity_circle_standard_model" method is implemented, which assumes the optic disk location
    within the eye model used RayOcular's default value.

    Parameters
    ----------
    geometry_generators : object
        An object containing geometry generation parameters, including eye laterality.
    eye_model_parameters : object
        An object containing parameters of the eye model, including optic nerve rotation.
    on_model_loc_method : str
        The method used to determine the ON model location. Currently, only "unity_circle_standard_model" is supported.

    Returns
    -------
    on_model_loc_patient : numpy.ndarray
        The location of the optic nerve in the eye model, adjusted for eye laterality.

    Raises
    ------
    AssertionError
        If the optic nerve (and thus the optic disk) has been manually rotated within the eye model, violating fit assumptions.
    NotImplementedError
        If the specified `on_model_loc_method` is not implemented.

    Notes
    -----
    - The function assumes the optic disk location has not been manually changed within the eye model.
    - Validation and additional testing for different eye models are recommended (see TODOs in code).
    """
    # TODO: validate this method further with multiple different types of eye models
    # TODO: add testing method for this methodology

    logger.debug("Starting calc_on_model_loc_patient function")

    if on_model_loc_method == "unity_circle_standard_model":
        # get the eyes laterality, as the location on the unity circle depends on the laterality.
        laterality = geometry_generators.Laterality

        # Check if the optic disk within the eye model was not shifted. This shift is denoted by the optic nerve rotation.
        normal_on_rotation_od = {"x": 2.5, "y": -17}
        normal_on_rotation_os = {"x": 2.5, "y": 17}

        on_rotation = eye_model_parameters.OpticalNerveRotation
        if (
            laterality == "Right"
            and (on_rotation["x"] != normal_on_rotation_od["x"] or on_rotation["z"] != normal_on_rotation_od["y"])
        ) or (
            laterality == "Left"
            and (on_rotation["x"] != normal_on_rotation_os["x"] or on_rotation["z"] != normal_on_rotation_os["y"])
        ):
            raise AssertionError(
                "Optic nerve (and thus disk) has been rotated manually within the eye model, which renders one of the fit assumptions incorrect"
            )

        if laterality == "Right":
            on_model_loc_patient = (
                Config.DEFAULT_OPTIC_NERVE_LOCATION
            )  # default location of the optic nerve location in the eye model of a RIGHT eye
        elif laterality == "Left":
            on_model_loc_patient = Config.DEFAULT_OPTIC_NERVE_LOCATION * np.array(
                [-1, 1, 1]
            )  # default location of the optic nerve location in the eye model of a LEFT eye

        return on_model_loc_patient

    raise NotImplementedError(
        f"{on_model_loc_method} is not implemented as a method to get the models location of the optic nerve for the fit input"
    )


def calc_residuals_for_registration_with_fitted_rotation(params, clip_data, optic_nerve_data, axes):
    """Calculate residuals for registration of ellipsoid model with fitted rotation.
    This function computes the residuals between a set of 3D points (clip_data) and a rotated, translated ellipsoid
    model,
    as well as the normalized squared distance between the predicted and observed optic nerve (ON) locations.

    Parameters
    ----------
    params : array-like, shape (6,)
        Model parameters. The first three elements are the center coordinates (x0, y0, z0) of the ellipsoid.
        The fourth and sixth elements are the rotation angles (in degrees) around the x and z axes, respectively.
        The y-axis rotation is fixed to zero.
    clip_data : ndarray, shape (N, 3)
        Array of 3D points representing the data to be fitted to the ellipsoid model.
    optic_nerve_data : tuple of ndarray
        Tuple containing:
            - on_model_loc: ndarray, shape (3,)
                The expected location of the optic disk (should be on the unit ellipsoid, see the docstrings of calc_on_model_loc_patient).
            - on_image_loc: ndarray, shape (3,)
                The observed location of the optic disk in the image data.
    axes : array-like, shape (3,)
        The semi-axes lengths of the eye model.

    Returns
    -------
    residuals : ndarray, shape (N+1,)
        Array containing:
            - The residuals for each point in `clip_data` (distance from the ellipsoid surface).
            - The normalized squared distance between the predicted and observed ON locations.
    """
    logger.debug("Starting registration_residuals function")

    # organize input
    x0, y0, z0 = params[:3]  # Center coordinates
    euler_angles = np.array([-params[3], 0, -params[5]])  # Rotation angles (fixing y-axis angle to zero)
    on_model_loc, on_image_loc = (
        optic_nerve_data  # model loc should be put in the same place as the image loc (the clicked POI)
    )

    # Rotation matrix
    rotation_matrix = Rotation.from_euler("xyz", euler_angles, degrees=True).as_matrix()

    # Translate data to the origin
    centered_clip_data = clip_data - np.array([x0, y0, z0])
    centered_on_image_loc = on_image_loc - np.array([x0, y0, z0])

    # Rotate data to align with principal axes
    rotated_clip_data = centered_clip_data @ rotation_matrix.T
    rotated_on_image_loc = centered_on_image_loc @ rotation_matrix.T

    # Ellipsoid equation residuals
    a, b, c = axes
    residuals_clips = (
        (rotated_clip_data[:, 0] / a) ** 2 + (rotated_clip_data[:, 1] / b) ** 2 + (rotated_clip_data[:, 2] / c) ** 2 - 1
    )

    # ON location residuals, normalised to the same distances as the clip residuals
    # first normalise the rotated_on_image_loc to the unity circle (as we do with the clip residuals as well)
    # note that the on_model_loc should already be on the unity circle
    rotated_on_image_loc_unity_circle = rotated_on_image_loc / axes  # divide the coordinates by the corresponding axes

    normalised_dist_on = sum((rotated_on_image_loc_unity_circle - on_model_loc) ** 2)

    logger.debug(
        "np.linalg.norm(rotated_on_image_loc_unity_circle - on_model_loc)= %s",
        np.linalg.norm(rotated_on_image_loc_unity_circle - on_model_loc),
    )
    logger.debug("rotated_on_image_loc_unity_circle= %s", rotated_on_image_loc_unity_circle)
    logger.debug("on_model_loc= %s", on_model_loc)
    logger.debug("residuals: %s", np.append(residuals_clips, normalised_dist_on))

    return np.append(residuals_clips, normalised_dist_on)


def calc_ellipsoid_registration_with_fitted_rotation(clip_data, on_model_loc, on_image_loc, axes, initial_guess=None):
    """Performs a least-squares optimization to register an ellipsoid to the provided
    clip data, fitting both the center and rotation angles based on the clip locations and the optic
    disk POI. The optimization minimizes the residuals between the transformed model and the observed data.

    Parameters
    ----------
    clip_data : np.ndarray
        An (N, 3) array of 3D points representing the data to fit.
    on_model_loc : np.ndarray
        A (3,) array specifying the location of the optic disk model.
    on_image_loc : np.ndarray
        A (3,) array specifying the location of the optic disk POI (based on the MR image).
    axes : np.ndarray
        A (3,) array representing the axes lengths of the ellipsoid.
    initial_guess : np.ndarray or None, optional
        Initial guess for the optimization parameters (center and rotation angles).
        If None, the center is initialized to the mean of `clip_data` and angles to zero.

    Returns
    -------
    fitted_center : np.ndarray
        A (3,) array representing the estimated center of the ellipsoid.
    fitted_angles : np.ndarray
        A (3,) array of rotation angles (in degrees) fitted to the data.

    Notes
    -----
    - This function relies on `calc_residuals_for_registration_with_fitted_rotation` for computing
    the residuals and uses `scipy.optimize.least_squares` for optimization.
    - The y rotation is set to 0
    """
    logger.debug("Starting calc_ellipsoid_registration function")

    if initial_guess is None:
        center_guess = np.mean(clip_data, axis=0)
        angles_guess = [0, 0, 0]
        initial_guess = np.hstack([center_guess, angles_guess])

    result = least_squares(
        calc_residuals_for_registration_with_fitted_rotation,
        initial_guess,
        args=(clip_data, (on_model_loc, on_image_loc), axes),
        verbose=0,
    )
    logger.debug("fit result: %s", result)
    fitted_center = result.x[:3]
    fitted_angles = np.array([result.x[3], result.x[4], result.x[5]])
    return fitted_center, fitted_angles


def calc_residuals_for_registration_with_calculated_rotation(
    params, clip_data, optic_nerve_data, axes, vitreous_body_center, eye_rotation_in, eye_translation_input
):
    """Calculate residuals for registration by computing distances from clip points to an ellipsoid.
    This function translates the clip data according to the provided center parameters, computes
    the necessary rotation to align the model with the observed optic nerve location, applies
    the rotation, and then calculates the residuals (distance to the ellipsoid surface) for each
    clip point.

    Parameters
    ----------
    params : array-like, shape (3,)
        The center coordinates (x0, y0, z0) to which the clip data should be translated.
    clip_data : ndarray, shape (N, 3)
        The 3D coordinates of the clip points.
    optic_nerve_data : tuple of array-like
        Tuple containing (on_model_loc, on_image_loc), where:
            on_model_loc : array-like, shape (3,)
                The optic disk location in the model.
            on_image_loc : array-like, shape (3,)
                The optic disk location in the image (clicked point of interest).
    axes : array-like, shape (3,)
        The ellipsoid axes lengths (rl_axis, is_axis, ap_axis).
    vitreous_body_center : array-like, shape (3,)
        The center of the vitreous body in the model.
    eye_rotation_in : dict
        Dictionary containing the current eye rotation angles in degrees, with keys "x" and "z" ("y"  is not used and should be set to 0).
    eye_translation_input : array-like, shape (3,)
        The initial translation/ center location of the eye model.

    Returns
    -------
    residuals_clips : ndarray, shape (N,)
        The residuals for each clip point, representing the distance to the ellipsoid surface.
        Values close to zero indicate points lying on the ellipsoid.
    """
    logger.debug("Starting registration_residuals function")
    logger.debug("params: %s", params)
    # organize input
    x0, y0, z0 = params  # Center coordinates
    on_model_loc, on_image_loc = (
        optic_nerve_data  # model loc should be put in the same place as the image loc (the clicked POI)
    )
    rl_axis, is_axis, ap_axis = axes

    # Translate clip data to the origin
    centered_clip_data = clip_data - np.array([x0, y0, z0])

    # calculate necessary rotation
    roll_angle_deg, pitch_angle_deg = calc_roll_and_pitch_of_shifted_eyemodel(
        vitreous_body_center, axes, on_model_loc, on_image_loc, eye_translation_input, params
    )

    # take current rotation into account
    roll_angle_deg = eye_rotation_in["z"] + roll_angle_deg
    pitch_angle_deg = eye_rotation_in["x"] + pitch_angle_deg

    # refactor into euler angles, y-axis angle (roll) to zero
    euler_angles = np.array([-pitch_angle_deg, 0, -roll_angle_deg])
    logger.debug("euler_angles: %s", euler_angles)

    # Rotation matrix
    rotation_matrix = Rotation.from_euler("xyz", euler_angles, degrees=True).as_matrix()
    logger.debug("rotation_matrix: %s", rotation_matrix)

    # Rotate data to align with principal axes
    rotated_clip_data = centered_clip_data @ rotation_matrix.T
    logger.debug("rotated_clip_data: %s", rotated_clip_data)

    logger.debug("calculated rotation: pitch %s", pitch_angle_deg)
    logger.debug("calculated rotation: roll %s", roll_angle_deg)

    # Ellipsoid equation residuals
    residuals_clips = (
        (rotated_clip_data[:, 0] / rl_axis) ** 2
        + (rotated_clip_data[:, 1] / is_axis) ** 2
        + (rotated_clip_data[:, 2] / ap_axis) ** 2
        - 1
    )

    logger.debug("residuals: %s", residuals_clips)

    return residuals_clips


def calc_ellipsoid_registration_with_calculated_rotation(
    clip_data,
    on_model_loc,
    on_image_loc,
    axes,
    vitreous_body_center,
    eye_rotation_in,
    eye_translation_in,
    initial_guess=None,
):
    """Registers an ellipsoid model to clip data using least squares optimization,
    incorporating calculated eye rotation and translation. Rotation is based purely on the
    location of the optic disk, while translation is based on the clip location. For each
    evaluated center translation, the corresponding rotation is calculated and thereafter,
    the residuals are calculated.

    Parameters
    ----------
    clip_data : np.ndarray
        Array of 3D points representing the clip data to be registered.
    on_model_loc : np.ndarray
        3D coordinates of the optic disk model center.
    on_image_loc : np.ndarray
        3D coordinates of the clicked POI of the optic disk on the MR image.
    axes : np.ndarray
        The axes lengths of the ellipsoid model.
    vitreous_body_center : np.ndarray
        The center coordinates of the vitreous body (which corresponds to the center of the eye/sclera ellipsoid).
    eye_rotation_in : np.ndarray
        Initial eye rotation parameters.
    eye_translation_in : np.ndarray
        Initial eye translation parameters.
    initial_guess : np.ndarray, optional
        Initial guess for the optimizer. If None, the mean of `clip_data` is used.

    Returns
    -------
    np.ndarray
        Optimized parameters resulting from the registration process.

    Notes
    -----
    This function uses `scipy.optimize.least_squares` to minimize the residuals
    computed by `calc_residuals_for_registration_with_calculated_rotation`.
    """
    logger.debug("Starting calc_ellipsoid_registration function")

    if initial_guess is None:
        initial_guess = np.mean(clip_data, axis=0)

    result = least_squares(
        calc_residuals_for_registration_with_calculated_rotation,
        initial_guess,
        args=(clip_data, (on_model_loc, on_image_loc), axes, vitreous_body_center, eye_rotation_in, eye_translation_in),
        verbose=0,
    )
    logger.debug("fit result: %s", result)
    return result.x


def calc_roll_and_pitch_of_shifted_eyemodel(
    retina_center_location, axes, on_model_loc, on_image_loc, eye_translation_before_shift, eye_translation_after_shift
):
    """Calculates the roll and pitch angles required to align a shifted eye model with observed optic disc positions.
    This function computes the roll and pitch corrections for an eye model after a translational shift, based on the
    locations of the retina center, retina axes, optic disc model center, and the optic disc point of interest (POI) as
    clicked on the MRI image.

    Parameters
    ----------
    retina_center_location : array-like, shape (3,)
        The (x, y, z) coordinates of the retina center in the original eye model.
    axes : array-like, shape (3,)
        The axes of the retina, typically representing the orientation in (x, y, z).
    on_model_loc : array-like, shape (3,)
        The (x, y, z) coordinates of the optic disc on the eye model.
    on_image_loc : array-like, shape (3,)
        The (x, y, z) coordinates of the optic disc POI as clicked on the MRI image.
    eye_translation_before_shift : array-like, shape (3,)
        The translation vector of the eye center before the shift.
    eye_translation_after_shift : array-like, shape (3,)
        The translation vector of the eye center after the shift.

    Returns
    -------
    roll_angle_deg : float
        The roll angle (in degrees) required to align the model with the observed optic disc position.
    pitch_angle_deg : float
        The pitch angle (in degrees) required to align the model with the observed optic disc position.

    Notes
    -----
    Coordinates are assumed to be in the (x, y, z) or (rl, ap, is) convention.
    The function corrects for translational shifts before calculating the required rotations.
    """
    # calculate the new location of the vitreous body, and on model
    eye_center_shift = eye_translation_before_shift - eye_translation_after_shift

    retina_center_after_shift = retina_center_location - eye_center_shift
    on_model_loc_after_shift = on_model_loc - eye_center_shift

    roll_angle_deg = match_sclera_to_markers.calc_rotation_to_align_points(
        retina_center=(retina_center_after_shift[0], retina_center_after_shift[1]),
        retina_axes=(axes[0], axes[1]),
        optic_disc_eyemodel=(on_model_loc_after_shift[0], on_model_loc_after_shift[1]),
        optic_disc_poi=(on_image_loc[0], on_image_loc[1]),
    )

    pitch_angle_deg = match_sclera_to_markers.calc_rotation_to_align_points(
        retina_center=(retina_center_after_shift[1], retina_center_after_shift[2]),
        retina_axes=(axes[1], axes[2]),
        optic_disc_eyemodel=(on_model_loc_after_shift[1], on_model_loc_after_shift[2]),
        optic_disc_poi=(on_image_loc[1], on_image_loc[2]),
    )

    return roll_angle_deg, pitch_angle_deg
