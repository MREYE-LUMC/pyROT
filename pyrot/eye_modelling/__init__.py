"""Eye modelling
=============

The eye_modelling module provides methods matching the geometric eye-model to imaging and biometry data.

Notes
-----
The methods used in this package are based on the work of Pors et al. (submitted)

Modules
-------
clipbased_model
    Match a clip-based eye model to the clips.
common_methods
    Shared utility functions and methods for eye modeling.
ellipsoid_fit
    Functions for fitting an ellipsoid to POIs.
match_sclera_to_markers
    Methods for matching sclera ellipse to POIs.
match_with_biometry
    Methods to determine the best-fitting eye-model based on imaging and biometry data.
"""

from __future__ import annotations

from pyrot.eye_modelling import (
    clipbased_model,
    common_methods,
    ellipsoid_fit,
    match_sclera_to_markers,
    match_with_biometry,
)

__all__ = ["clipbased_model", "common_methods", "ellipsoid_fit", "match_sclera_to_markers", "match_with_biometry"]
