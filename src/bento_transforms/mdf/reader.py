"""
Load MDF-flavored transformation YAML files to bento-meta objects
"""
from __future__ import annotations

import logging
import re
from .pymodels import (
    Defaults, PackageDefault,
    NPIdentitySpec,
    IdentitySpec, IdentityTransform,
    FromToList, GeneralTransform,
)
from pathlib import Path
from copy import deepcopy
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
        self._transforms = {}
        self._defaults = None
        self._package_default = None
        self._raise_error = raise_error
        self.parse_transforms_success = False
        if self.files:
            super().load_yaml()
        self.parse_transforms()

    @property
    def input_defaults(self):
        if self._defaults:
            return self._defaults.Inputs
        else:
            return None

    @property
    def output_defaults(self):
        if self._defaults:
            return self._defaults.Outputs
        else:
            return None
    
    def parse_transforms(self) -> None:
        self.parse_transforms_success = True
        if not self.mdf or not self.mdf.get("TransformDefinitions"):
            self.parse_transforms_success = False
            if raise_error:
                raise RuntimeError("No transforms MDF loaded")
            return self.parse_transforms_success
        tfdefns = self.mdf["TransformDefinitions"]
        if tfdefns.get("Defaults"):
            if tfdefns["Defaults"].get("Package"):
                (name, version) = re.match("^([^@]+)([@].*)",
                                           tfdefns["Defaults"]["Package"]).groups()
                tfdefns["Defaults"]["Package"] = PackageDefault(Name=name, Version=version[1:])
            self._defaults = Defaults(**tfdefns["Defaults"])
        if tfdefns.get("Identities"):
            self.parse_identities()

    def parse_identities(self) -> None:
        identities = []

        def convert_spec_to_ident(spec):
            ret = deepcopy(spec)
            if  ((ret['From'].get('Model') is None and self.input_defaults.Model is None) or
                 (ret['To'].get('Model') is None and self.output_defaults.Model is None)):
                RuntimeError(f"Model missing without defaults set (processing {spec})")
            if ret['From'].get('Model') is None:
                ret['From']['Model'] = self.input_defaults.Model
                ret['From']['Version'] = self.input_defaults.Version
            if ret['To'].get('Model') is None:
                ret['To']['Model'] = self.output_defaults.Model
                ret['To']['Version'] = self.output_defaults.Version
            if ret['From'].get('Node') is None:
                ret['From']['Node'] = self._defaults.Inputs.Node
            if ret['To'].get('Node') is None:
                ret['To']['Node'] = self._defaults.Outputs.Node
            if ret['From'].get('Props') is None:
                ret['From']['Props'] = [ret['From']['Prop']]
            if ret['To'].get('Props') is None:
                ret['To']['Props'] = [ret['To']['Prop']]
            return ret
            
        for spec in self.mdf["TransformDefinitions"]["Identities"]:
            if isinstance(spec, dict):
                ident = IdentitySpec(**convert_spec_to_ident(spec))
            elif isinstance(spec, list):
                if self.input_defaults is None and self.output_defaults is None:
                    RuntimeError(f"Simple identity format requires also setting input and output default models (processing {spec})")
                from_to = FromToList(items=spec)
                (frm, to) = from_to.items
                (from_node, from_prop) = re.match("^([^.]+[.])?(.*)", frm).groups()
                if from_node:
                    from_node = from_node[:-1]
                (to_node, to_prop) = re.match("^([^.]+[.])?(.*)", to).groups()
                if to_node:
                    to_node = to_node[:-1]
                ident = NPIdentitySpec(
                    From={"Node": from_node if from_node else self.input_defaults.Node,
                          "Prop": from_prop},
                    To={"Node": to_node if to_node else self.output_defaults.Node,
                        "Prop": to_prop})
            else:
                RuntimeError("Can't parse as an Identity: {spec}")
            identities.append(IdentitySpec(**convert_spec_to_ident(ident.model_dump())))

        for ident in identities:
            handle = f"{ident.From.Node}_{ident.From.Props[0]}_{ident.To.Node}_{ident.To.Props[0]}"
            self._transforms[handle] = IdentityTransform(Input=ident.From,
                                                         Output=ident.To)
                                                         
