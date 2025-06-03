"""Export eye model geometries and regions of interest from RayOcular."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from shutil import copy
from tempfile import TemporaryDirectory
from typing import Literal
from warnings import warn

from connect import get_current

from pyrot.eye_modelling.datamodels.models import EyeModel

logger = logging.getLogger(__name__)


def full_export(
    output_directory: Path | str,
    eyemodelnr: int,
    export_suffix: str,
    roi_export_unit: Literal["Millimeters", "Centimeters"],
):
    """Exports all relevant data for a given eye model to a structured output directory.
    This function gathers patient, case, and examination information, creates a uniquely named
    export directory, and exports ROI geometries, eye model data, and points of interest (POIs)
    for the specified eye model number.

    Parameters
    ----------
    output_directory : Path or str
        The base directory where the export folder will be created.
    eyemodelnr : int
        The identifier number of the eye model to export.
    export_suffix : str
        Suffix to append to exported files for identification.
    roi_export_unit : Literal["Millimeters", "Centimeters"]
        The unit to use when exporting ROI geometries.

    Returns
    -------
    None

    Notes
    -----
    - The export directory is named using the current date and time, patient name, case name,
      examination name, and eye model number.
    - The function assumes that the current patient, case, and examination are set and accessible.
    """

    patient = get_current("Patient")
    case = get_current("Case")
    examination = get_current("Examination")

    directory_name = slugify(
        f"{datetime.now().strftime('%Y%m%d-%H%M')}-{patient.Name}-{case.CaseName}-{examination.Name}-{eyemodelnr}",  # noqa: DTZ005
    )

    export_directory = Path(output_directory) / directory_name
    export_directory.mkdir(parents=True, exist_ok=True)

    structure_set = case.PatientModel.StructureSets[examination.Name]

    set_level_of_detail(patient, structure_set, level_of_detail=256)
    export_roi_geometries(
        structure_set,
        export_directory,
        slugify(examination.Name),
        export_suffix=export_suffix,
        roi_export_unit=roi_export_unit,
    )
    export_eye_model(structure_set, export_directory, eyemodelnr)
    export_pois(structure_set, export_directory, examination.Name)


def slugify(value: str) -> str:
    return re.sub(r"[^\w\-_\.\s]", "_", value)


def set_level_of_detail(patient, structure_set, level_of_detail: int):
    structure_set.GeometryGenerators[0].EyeModelParameters.EditEyeModelParameters(
        NewValues={"LevelOfDetail": [level_of_detail]}
    )
    patient.Save()


def export_roi_geometries(
    structure_set,
    output_directory: Path,
    examination_name: str,  # noqa: ARG001
    export_suffix: str,
    roi_export_unit: str,
):
    """Exports ROI geometries from a given structure set to STL files.
    The function iterates over the ROI geometries in the provided structure set, filters them based on the specified
    export suffix,
    and exports each selected geometry as an STL file to the specified output directory. Exported files are named
    according to the ROI name,
    with spaces replaced by underscores, and include the export unit in the filename.

    Parameters
    ----------
    structure_set : object
        The structure set containing ROI geometries. Must have a `RoiGeometries` attribute that supports key access.
    output_directory : Path
        The directory where the exported STL files will be saved.
    examination_name : str
        The name of the examination (not directly used in the function, but may be required for context).
    export_suffix : str
        If specified, only ROIs with names ending with this suffix will be exported. If empty, ROIs with automatically generated suffixes are excluded.
    roi_export_unit : str
        The unit to use when exporting the ROI geometry (e.g., "mm").

    Warns
    -----
    UserWarning
        If no STL files are found for a given ROI, or if multiple STL files are found (only the first is used).

    Notes
    -----
    - Exported STL files are named as `{ROI_name}_unit_{roi_export_unit}.stl`, with spaces in ROI names replaced by underscores.
    - Temporary directories are used during export to avoid filename conflicts.
    - The function assumes that each geometry object has an `ExportRoiGeometryAsSTL` method.
    """

    geometries = structure_set.RoiGeometries
    geometry_names = geometries.keys()

    with TemporaryDirectory(prefix="rayocular_export_geometry") as tempdir:
        temp_path = Path(tempdir)

        # geometries does not support items()
        for name in geometry_names:
            # check if this is an stl we want to export
            if export_suffix:
                # if an export suffix is defined, only export the ROIs with that suffix
                if not name.endswith(export_suffix):
                    logger.debug("export suffix is %s.\nThus, not exporting %s", export_suffix, name)
                    continue
            # if no export suffix is defined, do not export those ROIS that contain a suffix
            # NB this only keeps the suffixes in mind for ROI names as they are automatically generated by RayOcular
            elif any(name.endswith(f" ({i})") for i in range(10)):
                logger.debug("export suffix is %s.\nThus, not exporting %s", export_suffix, name)
                continue

            # Make sure no spaces are present in the export path
            export_name = name.replace(" ", "_")

            # Export geometries to a separate subfolder to avoid name conflicts when copying to the output directory
            export_path = temp_path / export_name
            export_path.mkdir()

            geometries[name].ExportRoiGeometryAsSTL(DestinationDirectory=str(export_path), OutputUnit=roi_export_unit)

            exported_stls = list(export_path.glob(f"{export_name}*.stl"))

            if not exported_stls:
                warn(f"No STL files found for {name=}, skipping.", stacklevel=2)
                continue

            if len(exported_stls) > 1:
                warn(f"Multiple STL files found for {name=}, using the first one.", stacklevel=2)

            copy(exported_stls[0], str(output_directory / f"{export_name}_unit_{roi_export_unit}.stl"))


def export_eye_model(structure_set, output_directory: Path, eyemodelnr: int):
    """Export an eye model to a JSON file.

    Parameters
    ----------
    structure_set : object
        The structure set containing geometry generators for the eye models.
    output_directory : Path
        The directory where the exported JSON file will be saved.
    eyemodelnr : int
        The index of the eye model to export from the structure set.

    Returns
    -------
    None
        This function does not return anything. It writes the eye model data to a JSON file.

    Notes
    -----
    The exported file will be named as "eye_model_{eyemodelnr}.json" and will contain
    the serialized data of the selected eye model.
    """

    eye_model = EyeModel.from_rayocular(structure_set.GeometryGenerators[eyemodelnr])

    with open(output_directory / f"eye_model_{eyemodelnr}.json", "w", encoding="utf-8") as f:
        json.dump(asdict(eye_model), f, indent=4)


def export_pois(structure_set, output_directory: Path, examination_name: str):
    """Exports points of interest (POIs) from a structure set to a JSON file.

    Parameters
    ----------
    structure_set : object
        The structure set containing POI geometries. Must have a `PoiGeometries` attribute.
    output_directory : Path
        The directory where the output JSON file ("pois.json") will be saved.
    examination_name : str
        The name of the examination to associate with each POI.

    Returns
    -------
    None
        This function does not return anything. It writes the POIs to a JSON file.

    Notes
    -----
    The output JSON file will contain a dictionary where each key is the POI name and the value is a dictionary
    with the POI's location, type, and associated examination name.
    """

    poi_gmtrs = list(structure_set.PoiGeometries)
    pois_export = {}
    for poi in poi_gmtrs:
        pois_export[poi.OfPoi.Name] = {"location": poi.Point, "type": poi.OfPoi.Type, "examination": examination_name}
    with open(output_directory / "pois.json", "w", encoding="utf-8") as f:
        json.dump(pois_export, f, indent=4)
