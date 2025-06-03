"""Configuration for pyROT."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


class Config:
    """Configuration for pyROT.

    Settings can be overwritten by scripts/customization.py, which is imported by `__common__.py`.
    """

    ELLIPSOID_FIT_MINIMUM_MATRIX_CONDITION: float = 100
    """Minimum value of the matrix inversion condition for ellipsoid fitting.

    The condition number is a measure of how sensitive the solution of a system of linear equations is to changes in the input data.
    If the condition number is larger than this value, the fit is considered unstable and the user is requested to add an additional input marker.
    """

    CLIP_THICKNESS: float = 0.03
    """The thickness of the clips that are used for treatment planning/ positioning.

    The thickness is given in cm.
    """

    MODIFY_COR_SEMI_AXIS: bool = True
    """Whether to modify the cornea semi-axis."""

    CORNEA_TYPE: Literal["spherical", "elliptical"] = "spherical"
    """What shape the cornea model should have."""

    MARKER_LOCATION: Literal["choroid", "clips", "nocorrection"] = "choroid"
    """Where the pois used for the sclera elllipse fit are clicked, can be 'choroid', 'sclera' or 'nocorrection'."""

    EYE_MODEL_NR: int = 0
    """The eye model number. Needs to be altered/ checked in the case of multiple eye models."""

    ROI_EXPORT_UNIT: Literal["Centimeter", "Millimeter"] = "Centimeter"
    """The unit in which ROIs are exported."""

    ROI_EXPORT_ROI_SUFFIX: str | None = None
    """The suffix after the roi name of the rois that need to be exported.

    By default, there is no suffix in RayOcular.
    In patients where multiple eye models are made OR when the roi names have been manually altered, a suffix may be present.
    None if no suffix after ROI name, ' (0)' if this is the suffix after the ROI name in RayOcular, and so on.
    """

    DEFAULT_OPTIC_NERVE_LOCATION: NDArray[np.float_] = np.array([0.26, 0.84, 0.04])
    """Default location of the optic nerve in the eye model of a RIGHT eye.

    The coordinates are corrected for the fact that coordinates are shown as PA so a minus sign should be added to the
    y coordinate.
    """

    IRIS_OUTER_RADIUS_TOLERANCE: float = 0.05
    """Maximum difference between model and measured iris outer radius."""

    ROI_NAME_OD: str = "OpticalDisc"
    """The name of the optical disc roi.

    Needs to be altered only if multiple eye models are present OR the roi name has been manually altered in RayOcular
    This is used for the eye rotation script.
    """

    ROI_NAME_VITREOUS: str = "VitreousBody"
    """The name of the vitreous body roi.

    Needs to be altered only if multiple eye models are present OR the roi name has been manually altered in RayOcular
    This is used for the eye rotation script .
    """
