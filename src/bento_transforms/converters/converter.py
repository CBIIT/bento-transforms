"""
bento_transforms.converters.Converter class
This object can convert _data values_ under one Model to _data values_
under another model, according to Transform information provided as
bento-meta Transform objects. The bento-meta objects can be created by reading from an
MDB or from an MDF-Tranform YAML file (using bento_transforms.mdf.TransformReader).
"""

from __future__ import annotations
from toolz import pipe, compose

class Converter:
    def __init__(self):
        
