import logging
import sys
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path

if find_spec("pyrot") is None:
    sys.path.append(str(Path(__file__).absolute().parent.parent))  # TODO: implement this via path.resolve() instead

from pyrot.logging import PyrotMessageBoxHandler

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Log to stdout, because RayStation prefixes logs to stderr with ERROR
stdout = logging.StreamHandler(sys.stdout)
stdout.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
root_logger.addHandler(stdout)
root_logger.addHandler(PyrotMessageBoxHandler())

logger = logging.getLogger(__name__)

customization_spec = find_spec("customization")

if customization_spec is not None:
    logger.info("Customization loaded from %s", customization_spec.origin)
    import_module("customization")
