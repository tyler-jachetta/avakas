"""
Avakas Built-In Project Flavors
"""

from .base import AvakasProject, AvakasGitProject
from .ansible import AvakasAnsibleProject
from .chef import AvakasChefProject
from .erlang import AvakasErlangProject
from .node import AvakasNodeProject
from .python_pep621 import AvakasPEP621Project

__all__ = [
    'AvakasProject',
    'AvakasGitProject',
    'AvakasAnsibleProject',
    'AvakasChefProject',
    'AvakasErlangProject',
    'AvakasNodeProject',
    'AvakasPEP621Project'
]
