"""Interface for communicating with the RayStation API."""

from __future__ import annotations

import contextlib
import logging
from typing import Optional

with contextlib.suppress(ImportError):
    from connect import get_current

logger = logging.getLogger(__name__)


def load_current_patient():
    """Loads and returns the current patient associated with the active examination.

    Returns
    -------
    Patient
        The patient object corresponding to the current case
    """
    return get_current("Patient")


def load_current_structureset():
    """Loads and returns the current StructureSet associated with the active examination.

    Returns
    -------
    StructureSet
        The StructureSet object corresponding to the current examination.
    """

    case = get_current("Case")
    examination = get_current("Examination")
    examination_name = examination.Name

    return case.PatientModel.StructureSets[examination_name]


def load_eyemodel(structure_set, eyemodelnr):
    """Load geometry generators and eye model parameters from a structure set.

    Parameters
    ----------
    structure_set : object
        The structure set containing geometry generators and eye model parameters.
    eyemodelnr : int
        The index of the eye model to load from the structure set.

    Returns
    -------
    geometry_generators : object
        The geometry generators for the specified eye model.
    eye_model_parameters : object
        The eye model parameters for the specified eye model.
    """
    geometry_generators = structure_set.GeometryGenerators[eyemodelnr]

    eye_model_parameters = geometry_generators.EyeModelParameters

    return geometry_generators, eye_model_parameters


def load_pois(structure_set, poi_type: Optional[str] = None, poi_name_contains: Optional[str] = None):
    """Load POIs (Points of Interest) from a structure set, optionally filtering by type or name substring.

    Parameters
    ----------
    structure_set : object
        The structure set containing POI geometries.
    poi_type : str, optional
        The type of POI to filter by. If provided, only POIs of this type are returned.
    poi_name_contains : str, optional
        A substring to search for in POI names. If provided, only POIs whose names contain this substring are returned.

    Returns
    -------
    list
        A list of POI geometries matching the specified criteria.
    """

    pois = structure_set.PoiGeometries

    if poi_type:
        pois = [pg for pg in pois if pg.Point is not None and pg.OfPoi.Type == poi_type]
    if poi_name_contains:
        pois = [pg for pg in pois if pg.Point is not None and poi_name_contains in pg.OfPoi.Name]

    return pois


def load_rois(structure_set, roi_type: Optional[str] = None, roi_name_contains: Optional[str] = None):
    """Load ROIs (Regions of Interest) from a structure set, optionally filtering by type or name substring.

    Parameters
    ----------
    structure_set : object
        The structure set containing ROI geometries. Must have a `RoiGeometries` attribute.
    roi_type : str, optional
        The type of ROI to filter by. If provided, only ROIs of this type are returned.
    roi_name_contains : str, optional
        A substring to filter ROI names. If provided, only ROIs whose names contain this substring are returned.

    Returns
    -------
    list
        A list of ROI geometries matching the specified filters.
    """

    rois = structure_set.RoiGeometries

    if roi_type:
        rois = [rg for rg in rois if rg.OfRoi.Type == roi_type]
    if roi_name_contains:
        rois = [rg for rg in rois if roi_name_contains in rg.OfRoi.Name]

    return rois


def update_eye_model(eye_model_generators, new_values):
    """Update the eye model parameters with new values.

    Parameters
    ----------
    eye_model_generators : object
        Object providing access to eye model parameter editing functionality.
    new_values : dict
        Dictionary containing the new parameter values to update the eye model with.
    """

    logger.debug("updating eye model with new eye model values %s:", new_values)
    eye_model_generators.EyeModelParameters.EditEyeModelParameters(NewValues=new_values)
