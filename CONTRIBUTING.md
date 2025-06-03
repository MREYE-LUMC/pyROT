# Contributing

Thank you for considering contributing to pyROT! pyROT aims to be a community-driven project and warmly accepts contributions. Please follow the contribution guidelines below before you open a Pull Request. If you have any questions, please email us (pyrot@mreye.nl) or [open a new discussion](https://github.com/MREYE-LUMC/pyROT/discussions).

# Code style

To ensure a consistent code style and quality, we have established the following guidelines:

- Please format your docstrings according to [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html).
- Lint and format your code using [hatch](https://hatch.pypa.io/latest/). The linting requirements differ slightly between `pyROT` and `scripts`, with the latter being less strict. The `pyROT` package is expected to be more mature and stable (eg. containing unit tests to guarantee similar performance across versions/centers). The `scripts` are smaller snippets of code to run within RaySearch, and some checks are therefore not applicable there (e.g. no type hints, no docstrings, etc.).


## On Hatch

We added a basic project configuration, including configuration for Hatch, a Python project management tool. This includes a configuration for linting. A GitHub CI pipeline has been added to automatically lint code on each commit (on GitHub itself, and it won't automatically fix anything; that you'll have to do locally)

Read more about Hatch here: https://hatch.pypa.io/latest/

### Installing Hatch

Hatch provides a Windows installer which you can download here: https://hatch.pypa.io/latest/install/#windows
However, for easier future upgrades and easy installation of other Python tools, we recommend using `uv`, a Python toolchain manager, instead.

Run this command in a terminal to install `uv`:

```pwsh
winget install astral-sh.uv
```

Restart your terminal so it knows about the existence of `uv`, then install Hatch using `uv`:

```pwsh
uv tool install hatch
```

Or, if you don't like installing tools, you can also run it without installing:

```pwsh
uvx hatch
```

### Linting and formatting code

You can lint and format code using the `hatch fmt` command.
Hatch will format all code and fix some errors itself. Errors it can't fix itself, will be listed in the output of the command.