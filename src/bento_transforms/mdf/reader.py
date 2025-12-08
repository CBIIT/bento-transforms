"""
Load MDF-flavored transformation YAML files to bento-meta objects
"""
from __future__ import annotations

import logging
from pathlib import Path
from bento_meta.objects import Node, Edge, Property, Tag, Term
from bento_meta.tf_objects import Transform, TfStep
from bento_mdf import MDFReader
from bento_mdf.mdf.convert import spec_to_entity

class TransformReader(MDFReader):
    """MDF class for reading the MDF-Transform format into bento-meta objects"""

    def __init__(
            self,
            *yaml_files: str | Path | list[str | Path],
            handle: str | None = None,
            mdf_schema: str | Path | None = None,
            raise_error: bool = False,
            logger: logging.Logger | None = None,
    ) -> None:
        self.files = yaml_files
        self.mdf = {}
        self.mdf_schema = mdf_schema
        self.handle = handle
        if self.files:
            super().load_yaml()
        
