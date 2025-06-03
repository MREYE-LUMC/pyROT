"""PyROT: Python RayOcular Tools.

A set of tools to work with eye models in Python. This library is designed to be as vendor-agnostic
as possible, allowing it to be used without RayStation. Interactions with RayStation are handled
through the `ro_interface` module.
"""

from __future__ import annotations

from pyrot import ro_interface

__all__ = ["ro_interface"]
