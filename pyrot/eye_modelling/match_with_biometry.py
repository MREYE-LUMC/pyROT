"""Match the eye model to biometry data."""

from __future__ import annotations

import logging
import math

from pyrot import ro_interface
from pyrot.config import Config

logger = logging.getLogger(__name__)


def calc_elliptical_cornea_radii(
    cornea_thickness: float,
    iris_outerradius: float,
    aqueous_depth: float,
    iris_thickness: float,
    shape_factor: float,
) -> tuple[float, float]:
    """Calculate the required cornea AP radius to have the required AD for an elliptical cornea model.

    Parameters
    ----------
    cornea_thickness : float
        Central corneal thickness (CCT) in cm.
    iris_outerradius : float
        Outer radius of the iris in cm.
    aqueous_depth : float
        Aqueous depth (posterior cornea to anterior lens) in cm.
    iris_thickness : float
        Thickness of the iris in cm.
    shape_factor : float
        Shape factor for the elliptical cornea model.

    Returns
    -------
    cornea_ap_radius : float
        Anterior-posterior radius of the cornea in cm.
    cornea_min_radius : float
        Minimum radius of the cornea in cm.
    """

    logger.debug("start calc_elliptical_cornea_radii function")

    # RayOcular defines the cornea based on its innerdiameter, but you specify the outer diameter
    # we set the LR/IS radii of the cornea ellipse based on a predefined shape factor and limbus_radius
    # and calculate the AP radius to  give the correct AD

    cornea_lr_is_outer_radius = shape_factor * iris_outerradius

    # minimal and maximal diameter in RayOcular are .5 cm and 1.5 cm, respectively
    minimal_diameter, maximal_diameter = 0.5, 1.5

    if cornea_lr_is_outer_radius > maximal_diameter:
        cornea_lr_is_outer_radius = maximal_diameter
        logger.warning(
            "cornea outer radius is too large (%s), set cornea radius to maximal value", cornea_lr_is_outer_radius
        )
    elif cornea_lr_is_outer_radius < minimal_diameter:
        cornea_lr_is_outer_radius = minimal_diameter
        logger.warning("cornea radius too small (%s), set cornea radius to minimal value", cornea_lr_is_outer_radius)
    logger.debug("new cornea IS/LR semiaxis: %.3f", cornea_lr_is_outer_radius)

    # note that the cornea-iris intersection is defined at the front of the iris and the inner radius of the cornea
    cornea_lr_is_innerradius = cornea_lr_is_outer_radius - cornea_thickness

    ad_eff = (
        aqueous_depth - iris_thickness
    )  # as the cornea cross-section is obtained at the front iris plane, while the lens is at the back plane
    logger.debug("ad_eff: %s", ad_eff)

    # calculate ap inner radius (refer to documentation for the formulation of this formula)
    cor_ap_innerradius = (
        ad_eff
        * cornea_lr_is_innerradius
        / (cornea_lr_is_innerradius - math.sqrt((cornea_lr_is_innerradius**2) - iris_outerradius**2))
    )
    cornea_ap_outer_radius = cor_ap_innerradius + cornea_thickness

    return cornea_ap_outer_radius, cornea_lr_is_outer_radius


def calc_spherical_cornea_radii(
    cornea_thickness: float,
    iris_outerradius: float,
    aqueous_depth: float,
    iris_thickness: float,
) -> float:
    """Determine the cornea radii for a spherical cornea based on a specific AD and limbus radius.
    r = (a^2 + b^2)/2a with a = distance posterior corneal surface to anterior iris surface and b = limbus radius
    see also the folder 'documentation'.

    Parameters
    ----------
    iris_outerradius : float
        Outer radius of the iris in cm.
    aqueous_depth : float
        Aqueous depth (posterior cornea to anterior lens) in cm.
    iris_thickness : float
        Thickness of the iris in cm.
    cornea_thickness : float
        Central corneal thickness in cm.

    Returns
    -------
    cornea_outerradius : float
        Outer radius of the cornea in cm. Only one radius as the cornea model is a sphere.
    """

    logger.debug("start calc_spherical_cornea_radii function")

    cornea_to_front_iris = (
        aqueous_depth - iris_thickness
    )  # Distance from posterior corneal surface to middle of iris = a

    cornea_innerradius = (cornea_to_front_iris**2 + iris_outerradius**2) / (2 * cornea_to_front_iris)

    return cornea_innerradius + cornea_thickness


def calc_iris_outerradius(
    sclera_lr_outer_radius: float,
    sclera_is_outer_radius: float,
    sclera_ap_outer_radius: float,
    sclera_thickness: float,
    vitreous_depth_incl_lens: float,
    iris_thickness: float,
    retina_thickness: float,
) -> float:
    """Calculate the required iris outer radius to have the correct vitreous depth (including lens and retina).

    Parameters
    ----------
    sclera_lr_outer_radius : float
        Outer sclera semi-axis length in the left-right direction in cm.
    sclera_is_outer_radius : float
        Outer sclera semi-axis length in the inferior-superior direction in cm.
    sclera_ap_outer_radius : float
        Outer sclera semi-axis length in the anterior-posterior direction in cm.
    sclera_thickness : float
        Thickness of the sclera in cm.
    vitreous_depth_incl_lens : float
        Vitreous depth including lens in cm.
    iris_thickness : float
        Thickness of the iris in cm.

    Returns
    -------
    iris_outerradius : float
        Outer radius of the iris in cm.
    """

    logger.debug("start calc_iris_outerradius function")

    # convert outer radii (as specified by RayOcular) to innerradii (where the intersections are located)
    sclera_min_outer_radius = min(sclera_lr_outer_radius, sclera_is_outer_radius)
    sclera_min_innerradius = sclera_min_outer_radius - sclera_thickness
    sclera_ap_innerradius = sclera_ap_outer_radius - sclera_thickness

    # calculate the effective depth: the distance from the middle of the iris to the center of the sclera ellipse

    # As the posterior half of the vitreous is already included, we only need the front part
    # Additionally, the intersection is defined at half the iris thickness
    # Additionally the retina thickness needs to be added, as it is not included in the vitreous depth
    # but iris continues to the inner sclera boundary

    vitr_incl_lens_retina_and_half_iris = vitreous_depth_incl_lens + 0.5 * iris_thickness + retina_thickness
    effective_depth = vitr_incl_lens_retina_and_half_iris - sclera_ap_innerradius

    logger.debug("vitreous_depth_incl_lens: %s", vitreous_depth_incl_lens)
    logger.debug("vitreous incl lens, retina and half iris: %s", vitr_incl_lens_retina_and_half_iris)
    logger.debug("sclera_min_innerradius: %s", sclera_min_innerradius)
    logger.debug("sclera_ap_innerradius: %s", sclera_ap_innerradius)
    logger.debug("effective_depth: %s", effective_depth)
    logger.debug("effective_depth/sclera_ap_innerradius: %s", (effective_depth / sclera_ap_innerradius))

    return sclera_min_innerradius * math.sqrt(1 - (effective_depth**2) / (sclera_ap_innerradius**2))


def match_eye_model(
    eye_model_generators: object, eye_model_parameters: object, biometry_data: dict, cornea_type: str
) -> None:
    """Match the eye model parameters with the provided biometry data.
    Make the iris outerradius such that the vitreous length is correct
    and subsequently make the cornea radii such that the AD is correct.

    Parameters
    ----------
    eye_model : object
        The eye model object from RayOcular.
    eye_model_parameters : object
        An object containing specific eye model parameters
    biometry_data : dict
        Dictionary containing biometry measurements.
    cornea_type : str
        Type of cornea model ('elliptical' or 'spherical').
        'elliptical' gives an elliptical model where the AP radius differs from the LR and IS radii, which are equal
        'spherical' gives a spherical model

    Raises
    ------
    NotImplementedError
        If an unsupported cornea type is provided.
    """

    logger.debug("start match_eye_model function")

    # Get relevant eye-model parameters from RayOcular
    # sclera radii within RayOcular are defined as the outer radii
    sclera_lr_outer_radius = eye_model_parameters.ScleraSemiAxis["x"]
    sclera_is_outer_radius = eye_model_parameters.ScleraSemiAxis["z"]
    sclera_ap_outer_radius = eye_model_parameters.ScleraSemiAxis["y"]
    sclera_thickness = eye_model_parameters.ScleraThickness
    iris_thickness = eye_model_parameters.IrisThickness
    lens_radii = eye_model_parameters.LensSemiAxis
    retina_thickness = eye_model_parameters.RetinaThickness

    # Convert relevant biometry measurements
    cornea_thickness = biometry_data["CCT"]
    aqueous_depth = biometry_data["AD"] + biometry_data["AD_offset"]
    if biometry_data["AD_offset"] != 0:
        logger.info("Based on input data, used AD offset of %.3f mm", biometry_data["AD_offset"] * 10)
    vitreous_depth_incl_lens = biometry_data["AL"] - aqueous_depth - cornea_thickness
    lens_thickness = biometry_data["LT"]

    # Calculate iris outer radius
    logger.debug("Calculating iris outer radius")
    iris_outerradius = calc_iris_outerradius(
        sclera_lr_outer_radius=sclera_lr_outer_radius,
        sclera_is_outer_radius=sclera_is_outer_radius,
        sclera_ap_outer_radius=sclera_ap_outer_radius,
        sclera_thickness=sclera_thickness,
        vitreous_depth_incl_lens=vitreous_depth_incl_lens,
        iris_thickness=iris_thickness,
        retina_thickness=retina_thickness,
    )
    logger.debug("iris_outerradius: %s", iris_outerradius)

    # check that the iris outer radius matches the input (as this, if it is based on the wtw, is affected by some complicated steps including linear interpolation)
    if not math.isclose(iris_outerradius, biometry_data["WTW"] / 2, abs_tol=Config.IRIS_OUTER_RADIUS_TOLERANCE):
        logger.warning(
            "input WTW semi-diameter (%.4f) differs >= %.4f  cm from output (%.4f)",
            biometry_data["WTW"] / 2,
            Config.IRIS_OUTER_RADIUS_TOLERANCE,
            iris_outerradius,
        )
    else:
        logger.debug("input WTW is within %.3f cm from output iris radius", Config.IRIS_OUTER_RADIUS_TOLERANCE)
    # Calculate corneal curvature
    if cornea_type == "elliptical":
        logger.debug("Calculating cornea AP radius for an elliptical cornea model")
        shape_factor = 1.35  # Determined empirically
        cornea_ap_outer_radius, cornea_lr_is_outer_radius = calc_elliptical_cornea_radii(
            cornea_thickness=cornea_thickness,
            iris_outerradius=iris_outerradius,
            aqueous_depth=aqueous_depth,
            iris_thickness=iris_thickness,
            shape_factor=shape_factor,
        )
        cornea_lr_outer_radius, cornea_is_outer_radius = cornea_lr_is_outer_radius, cornea_lr_is_outer_radius
    elif cornea_type == "spherical":
        logger.debug("Finding the radii for a spherical cornea model")
        cornea_outer_radius = calc_spherical_cornea_radii(
            cornea_thickness=cornea_thickness,
            iris_outerradius=iris_outerradius,
            aqueous_depth=aqueous_depth,
            iris_thickness=iris_thickness,
        )
        cornea_lr_outer_radius, cornea_is_outer_radius, cornea_ap_outer_radius = (
            cornea_outer_radius,
            cornea_outer_radius,
            cornea_outer_radius,
        )
    else:
        raise NotImplementedError('Unsupported cornea type input, please input "elliptical" or "spherical".')

    # minimal and maximal diameter in RayOcular are .5 cm and 1.5 cm, respectively
    minimal_diameter, maximal_diameter = 0.5, 1.5

    logger.debug("Cornea AP radius: %.3f", cornea_ap_outer_radius)
    if cornea_ap_outer_radius > maximal_diameter:
        logger.warning("Cornea AP radius too large, setting to 1.5 cm")
        cornea_ap_outer_radius = maximal_diameter
    if cornea_ap_outer_radius < minimal_diameter:
        logger.warning("Cornea AP radius too small, setting to 0.5 cm")
        cornea_ap_outer_radius = minimal_diameter

    # Update eye model
    new_values = {
        "IrisOuterSemiAxis": [iris_outerradius, 0, iris_outerradius],
        "CorneaSemiAxis": [cornea_lr_outer_radius, cornea_ap_outer_radius, cornea_is_outer_radius],
        "LensSemiAxis": [lens_radii["x"], 0.5 * lens_thickness, lens_radii["z"]],
        "CorneaThickness": [cornea_thickness],
        "LensCorneaDistance": [cornea_thickness + aqueous_depth],  # Defined with respect to anterior cornea apex
    }

    logger.debug("updating eyemodel with new eye model values: %s", new_values)
    ro_interface.update_eye_model(eye_model_generators, new_values)


# ---
def get_eye_model_geometry(eye_model, structure_type):
    return next(
        rg
        for rg in eye_model.EyeModelParameters.AssociatedRoiGeometries
        if rg.GeneratedGeometryStatus.GeneratedStructureType == structure_type
    )
