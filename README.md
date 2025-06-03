# pyROT: Python RayOcular Tools

[![PyPI - Version](https://img.shields.io/pypi/v/rayocular-toolbox)](https://pypi.org/project/rayocular-toolbox)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FMREYE-LUMC%2FpyROT%2Fmain%2Fpyproject.toml)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/MREYE-LUMC/pyROT/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/pyrot/badge/?version=latest)](https://pyrot.readthedocs.io/en/latest/?badge=latest)

Python RayOcular Tools is a Python library to complement RayOcular, an eye-specific module of RaySearch.
It currently consists of three parts:

1. `pyROT` itself, which is Python package provides a set of tools to work with eye models in Python. This library is designed to be as vendor-agnostic as possible, allowing it to be used without RaySearch. Interactions with RaySearch are handled through `pyrot.ro_interface`;
2. `scripts` contains a set of scripts that can be run from within RaySearch and perform common tasks, such as generating eye models. These scripts import the `pyROT` package for all calculations.
3. `standalone`, as set of Python scripts that can be used without RaySearch, for example to analyse a large set of eye models (still to be added).

In addition, we hope that the pyROT repository will provide a platform to exchange methods and scripts within the ocular Proton Therapy community.


## Warranty and liability

The code is provided as is, without any warranty. It is solely intended for research purposes. No warranty is given and
no rights can be derived from it, as is also stated in the [MIT license](LICENSE).


## Contributing

pyROT aims to be a community-driven project and warmly accepts contributions.
If you want to contribute, please email us (pyrot@mreye.nl), [open a new discussion](https://github.com/MREYE-LUMC/pyROT/discussions) or read the [contribution guidelines](CONTRIBUTING.md) prior to opening a Pull Request.

## Installation

to be added

## Documentation

A preliminary version of the documentation is hosted on [Read the Docs](https://pyrot.readthedocs.io/en/latest/).

## Future ideas

- Extend the `pyROT` package with more tools, such as to determine the optimal gazing angle for a given eye model.
- Extend the unit tests to cover more of the `pyROT` package.