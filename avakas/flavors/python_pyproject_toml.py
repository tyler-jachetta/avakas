"""
Avakas built-in PEP 621 Python `pyproject.toml` flavor
[PEP 621 -- Storing project metadata in pyproject.toml](https://www.python.org/dev/peps/pep-0621/)
"""

import os.path
import re
import toml

from avakas.flavors.base import AvakasProject
from avakas.avakas import register_flavor
from avakas.errors import AvakasError
from avakas.utils import match_and_rewrite_lines

PROJECT_FILE_NAME = 'pyproject.toml'

@register_flavor('python-pyproject.toml')
class AvakasPyprojectDotTomlProject(AvakasProject):
	PROJECT_TYPE = "Python (pyproject.toml)"

	def guess_flavor(self):
        return os.path.isfile(os.path.join(self.directory, PROJECT_FILE_NAME))