from __future__ import annotations

import logging

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from pyrot import ro_interface
from pyrot.config import Config

logger = logging.getLogger(__name__)


def match_ellipse_with_pois(
    eye_model_generators, eye_model_parameters, structure_set, input_ellipse, poi_type_clips, poi_type_on
):
    # matches the translation and rotation of the eye model such that it corresponds to the known clip locations (on the outside of the sclera) and optic disk location

    logger.debug("Starting match_ellipse_with_pois function")

    eye_translation = eye_model_parameters.EyeTranslation
    eye_translation_input = [eye_translation["x"], eye_translation["y"], eye_translation["z"]]

    # get marker locations
    poi_geometries = ro_interface.load_pois(structure_set, poi_type=poi_type_clips)
    markers_in_patient = [np.array([pg.Point["x"], pg.Point["y"], pg.Point["z"]]) for pg in poi_geometries]

    on_model_loc_patient = calc_on_model_loc_patient(
        eye_model_generators, eye_model_parameters, "unity_circle_standard_model"
    )

    # find the POI clicked at the location of the OD on the MRI-image. This is the location on the choroid, so it should correspond to the OD in the eye model directly
    # make sure there is exactly one of the designated POI type
    on_image_loc_list = ro_interface.load_pois(structure_set, poi_type=poi_type_on)
    if len(on_image_loc_list) != 1:
        raise ValueError(f"ERROR: multiple or no POIs of type {poi_type_on} exist")
    on_image_loc = on_image_loc_list[0]
    on_image_loc_patient = np.array([on_image_loc.Point["x"], on_image_loc.Point["y"], on_image_loc.Point["z"]])

    # radii of the ellipse to be fitted to the POI's
    if input_ellipse == "sclera_radii":
        sclera_radii = eye_model_parameters.ScleraSemiAxis
        # note that the pois are clicked at the center of the clips, which means we should subtract .5*clip_thickness to get the real sclera radii
        clip_thickness = 0.02  # cm, .2 mm
        axes = (
            sclera_radii["x"] + (0.5 * clip_thickness),
            sclera_radii["y"] + (0.5 * clip_thickness),
            sclera_radii["z"] + (0.5 * clip_thickness),
        )
    else:
        raise NotImplementedError(f"input_ellipse {input_ellipse} not implemented")

    # fit the best location for the ellipsoid to minimize distance from POIs, setting rotation input to 0
    eye_translation_output, eye_rotation_output = calc_ellipsoid_registration(
        markers_in_patient,
        on_model_loc_patient,
        on_image_loc_patient,
        axes,
        initial_guess=[*eye_translation_input, 0, 0, 0],
    )

    # Update eye model
    new_values = {}
    new_values["EyeTranslation"] = eye_translation_output
    new_values["EyeRotation"] = eye_rotation_output
    logger.debug("updating eyemodel with new eye model values %s:", new_values)
    eye_model_generators.EyeModelParameters.EditEyeModelParameters(NewValues=new_values)


def calc_on_model_loc_patient(geometry_generators, eye_model_parameters, on_model_loc_method):
    # calculates the on_model_loc, so the location of the ON roi on the unity circle.
    # for the fit, we need the location of the optic disk if the eye model was situated on [0,0,0] with input angles [0,0,0] and sclera radii of [1,1,1].
    # we need this exact optic disk location because we also standardize the axes and poi locations in the sclera location fit method to the unity circle
    # (see registration_residuals())
    # currently, the only implemented method is based on the assumption that the optic disk location within the eye model has not been manually changed.

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


def registration_residuals(params, clip_data, optic_nerve_data, axes):
    # retuns residuals (distances to the ellipsoid & normalised distance between model and POI of Optic Disc/Nerve (ON))

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


def calc_ellipsoid_registration(clip_data, on_model_loc, on_image_loc, axes, initial_guess=None):
    logger.debug("Starting calc_ellipsoid_registration function")

    if initial_guess is None:
        center_guess = np.mean(clip_data, axis=0)
        angles_guess = [0, 0, 0]
        initial_guess = np.hstack([center_guess, angles_guess])

    result = least_squares(
        registration_residuals, initial_guess, args=(clip_data, (on_model_loc, on_image_loc), axes), verbose=0
    )
    logger.debug("fit result: %s", result)
    fitted_center = result.x[:3]
    fitted_angles = np.array([result.x[3], result.x[4], result.x[5]])
    return fitted_center, fitted_angles
