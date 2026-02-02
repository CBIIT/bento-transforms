"""
liftover.py - read and convert CCDI liftover mapping files
"""
import pandas as pd
import re
from typing import TextIO
from ..mdf.pymodels import (
    GeneralTransform,
    IdentityTransform,
    IOSpec,
    )


class Liftover(object):

    def __init__(self, tsv_file: str | TextIO):
        self.df = None
        self._from_model = None
        self._to_model = None
        self._transforms = None
        self.df = pd.read_csv(tsv_file, sep="\t")
        if isinstance(tsv_file, str):
            name = tsv_file
        else:
            name = tsv_file.name
        try:
            (from_model, to_model) = re.findall("([a-zA-Z]+)-model", name)
            from_model = from_model.upper()
            to_model = to_model.upper()
        except ValueError:
            pass
        from_version = self.df["lift_from_version"].dropna().unique().tolist()
        to_version = self.df["lift_to_version"].dropna().unique().tolist()
        if len(from_version) == 1:
            self._from_model = (from_model, from_version[0])
        else:
            raise ValueError("lift_from_version not unique")
        if len(to_version) == 1:
            self._to_model = (to_model, to_version[0])
        else:
            raise ValueError("lift_to_version not unique")

    @property
    def from_model(self):
        return self._from_model

    @property
    def to_model(self):
        return self._to_model
    
    @property
    def transforms(self):
        if self._transforms is None:
            self._parse_liftover()
        return self._transforms
        
    def _parse_liftover(self):
        self._transforms = {}
        for row in self.df.itertuples():
            if all([isinstance(row.lift_from_node, str),
                   isinstance(row.lift_from_property, str),
                   isinstance(row.lift_to_node,str),
                   isinstance(row.lift_to_property,str)]):
                hdl = f"{row.lift_from_node}_{row.lift_from_property}_to_"
                f"{row.lift_to_node}_{row.lift_to_property}"
                self._transforms[hdl] = IdentityTransform(
                    Inputs=[IOSpec(
                        Model=self.from_model[0],
                        Version=self.from_model[1],
                        Node=row.lift_from_node,
                        Props=[row.lift_from_property])],
                    Outputs=[IOSpec(
                        Model=self.to_model[0],
                        Version=self.to_model[1],
                        Node=row.lift_to_node,
                        Props=[row.lift_to_property])]
                )
