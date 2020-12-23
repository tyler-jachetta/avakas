"""
Avakas built-in PEP 621 Python `pyproject.toml` flavor
[PEP 621 -- Storing project metadata in pyproject.toml]
    (https://www.python.org/dev/peps/pep-0621/)
"""

import functools
import operator
import os.path
import toml

from avakas.flavors.base import AvakasProject
from avakas.avakas import register_flavor
from avakas.errors import AvakasError
from avakas.utils import match_and_rewrite_lines

PROJECT_FILE_NAME = 'pyproject.toml'
VERSION_KEY = 'version'


def _invalid_on_synonym(synonym):
    raise AssertionError('add_synonym is not valid on a synonym itself')


@register_flavor('python-pep621.toml')
class AvakasPEP621Project(AvakasProject):
    """
    Avakas project flavor to handle PEP 621 compliant Python

    PEP 621 defines two configuration vars in addition to the top level
    `'version`', which may be used in place of it. These are from Poetry and
    Setuptools (as well as flit, which does not store its version in the
    pyproject.toml). As these need to be handled differently, while retaining a
    valid base PEP 621 project, has me using a solution with some sort of
    plug-in subflavors.

    This is also the sort of crap I like to make for jollies, so probably belt
    and suspendered to all hell - HB 20201204

    The basic end result of the subflavors is that the parent/base flavor will
    never return true from `.guess_flavor()` if any of its synonyms'
    `.guess_flavor_static(<dir>)` returns true.

    ### Usage

    Adding a subflavor/synonym:

    ```
    # Two decorators...
    ## The outermost decorator registers the flavor as its own Avakas flavor
    @register_flavor('python-setuptools')
    ## The inner decorator registers the synonym as a synonym of the base
    ## flavor.
    @AvakasPEP621Project.add_synonym
    class AvakasPEP621SubFlavor(AvakasPEP621Project):

        PROJECT_TYPE = "Python - <details>"

        # A subflavor/synonym **MUST** expose a static or class method
        #   `add_synonym()` which accepts a single positional argument: a
        #   directory to check the flavor against.
        @staticmethod
        def guess_synonym_helper(directory):

        def guess_flavor(self, direcotry=None):
            if directory is None: directory = self.directory
    ```

    """
    __synonyms = set()

    PROJECT_TYPE = "Python (PEP 621 compliant pyproject.toml)"
    BUILD_BACKEND = None
    VERSION_KEYS = ['version']

    @classmethod
    def add_synonym(cls, synonym):
        if synonym is cls:
            raise AssertionError(
                'it is invalid to add a flavor as a synonym of itself.')
        cls.__synonyms.add(synonym)

        synonym.add_synonym = _invalid_on_synonym
        synonym.get_synonyms = lambda self: set()

        return synonym

    @classmethod
    def get_synonyms(cls):
        return cls.__synonyms

    def __init__(self, *args, **kwargs):

        super(AvakasPEP621Project, self).__init__(*args, **kwargs)

        self.pyproject_toml = os.path.join(self.directory, PROJECT_FILE_NAME)

    def _guess_flavor_from_config_dict(
            self, config=None, exception_on_no_version=True, **values):

        if config is None:
            with open(self.pyproject_toml, 'r') as fh:
                config = toml.load(fh)


        # Check the build system

        # Check the version key .
        # Since version should be expected to exist, Exception is raised by default

        try:
            functools.reduce(operator.getitem, self.VERSION_KEYS, config)
        except KeyError:
            if exception_on_no_version:
                Raise KeyError(f"{self.pyproject_toml} does not contain a version! ({'.'.join(self.VERSION_KEYS)}")


        return True

    def guess_flavor(self):
        """
        Check whether the project is a base-flavor PEP 621 metadata
        file (not a registered subflavor)

        This first checks whether any subflavors want to claim this,
        and, if not, it checks for the existence of a `pyproject.toml`
        file.
        """

        if not os.path.isfile(self.pyproject_toml):
            return False

        if any(
                Syn(directory=self.directory).guess_flavor()
                for Syn in self.get_synonyms()):
            return False

        return self.guess_flavor_from_config()

    def get_version(self):
        with open(self.pyproject_toml, 'r') as file_handle:
            toml_content = toml.load(file_handle)
            try:
                return toml_content[VERSION_KEY]
            except KeyError:
                # Version not defined
                import pdb
                pdb.set_trace()
                raise AvakasError('`pyproject.toml` does not define a version')
            except toml.TomlDecodeError:
                # Malformed toml
                raise AvakasError('`pyproject.toml` is malformed')

    def set_version(self, version, sanity_check=True):
        """
        Set the version in a pyproject.toml file.

        In an ideal world, I could just toml.edit_value and have it not touch
        any of the comments, etc., but today is not that day.

        Arguments:
            *version* (`str`): String representing the semantic version
            *sanity_check* (`bool`, optional) set this to `False` to disable
                the sanity check done (to ensure that nothing other than the
                desired value changed, as TOML so graciously provides comments,
                and it would be a shame to squander that to bump a
                value).

        Raises:
            AssertionError: Raised if the sanity check fails, which probably
                means that something went terribly wrong.

        Returns:
            *updated*: Returns `True` if an update needed to be made, and \
                `False` if the file already contained the desired version.

        Authors:
            * Tyler Jachetta <tjachetta@imgix.com>
        """

        with open(self.pyproject_toml, 'r') as file_handle:
            orig_content = toml.load(file_handle)
            file_handle.seek(0)
            lines, updated = match_and_rewrite_lines(
                r'^\s*version\s*=\s*\"(.*)\"\s*$',
                file_handle, version)
        if not updated:
            return False

        with open(self.pyproject_toml, 'w') as file_handle:
            file_handle.write('\n'.join(lines))

        if sanity_check:
            with open(self.pyproject_toml, 'r') as file_handle:
                expected_dict = dict(orig_content, version=version)
                assert toml.load(file_handle) == expected_dict

        return True


@register_flavor('python-setuptools')
@AvakasPEP621Project.add_synonym
class AvakasPEP621SetuptoolsProject(AvakasPEP621Project):

    PROJECT_TYPE = "Python (PEP 621 compliant pyproject.toml and setuptools)"
    BUILD_BACKEND = 'setuptools.build_meta'

    @staticmethod
    def guess_synonym_helper(directory):
        py_project_file = os.path.join(directory, PROJECT_FILE_NAME)
        if not os.path.isfile(py_project_file):
            return False

        with open(py_project_file, 'r') as fh:
            try:
                config = toml.load(fh)
            except toml.decoder.TomlDecodeError:
                return False

        return 'tool'

    def guess_flavor(self):
        return self.guess_synonym_helper(self.directory)


@register_flavor(python-poetry)
@AvakasPEP621Project.add_synonym
class AvakasPEP621PoetryProject(AvakasPEP621Project):

    PROJECT_TPYE = "Python project maanaged by Poetry"
    BUILD_BACKEND = r'poetry\.core.*'

    @staticmethod
    def guess_synonym_helper(directory):
        py_project_file = os.path.join(directory, PROJECT_FILE_NAME)
        if not os.path.isfile(py_project_file):
            return False

        with open(py_project_file, 'r') as fh:
            try:
                config = toml.load(fh)
            except toml.decoder.TomlDecodeError:
                return False

        try:
            config['tool']['poetry']['version']
        except KeyError:
            return False
