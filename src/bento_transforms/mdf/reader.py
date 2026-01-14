"""
bento_transforms.mdf.reader

Validate and Load MDF-flavored transformation YAML files to a dict
of standardized Pydantic GeneralTransform instances
"""
from __future__ import annotations

import logging
import re
from .pymodels import (
    Defaults, EntityDefaults, PackageC,
    IOSpec, TfStepSpec,
    IdentitySpec, IdentityTransform,
    FromToList, GeneralTransform,
)
from typing import List
from pathlib import Path
from bento_mdf import MDFReader

from pdb import set_trace


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
        if self.files:
            super().load_yaml()
        self.parse_mdf()

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

    @property
    def package_default(self):
        if self._defaults:
            return self._defaults.Package
        else:
            return None

    @property
    def transforms(self):
        return self._transforms
    
    def convert_dict_to_IOSpec(self, spec: dict | List[dict],
                               defaults: EntityDefaults) -> List[IOSpec]:
        def set_defaults_or_die(spec, attr):
            if spec.get(attr) is None:
                if defaults is None or defaults.__getattribute__(attr) is None:
                    raise RuntimeError(f"{attr} not specified and no default set (processing {spec})")
                spec[attr] = defaults.__getattribute__(attr)
            return
        
        if isinstance(spec, dict):
            spec = [spec]
        ret = []
        for s in spec:
            for attr in ["Model", "Version", "Node"]:
                set_defaults_or_die(s, attr)

            if s.get("Prop") is not None:
                s["Props"] = [s["Prop"]]
            if s.get("Props") is None:
                raise RuntimeError(f"Props value is required (processing {spec})")
            if isinstance(s["Props"], str):
                s["Props"] = [s["Props"]]
            ret.append(IOSpec(**s))
        return ret
            
    def convert_string_to_IOSpec(self, spec: str | List[str],
                                 defaults: EntityDefaults | None ) -> List[IOSpec]:
        if defaults is None:
            raise RuntimeError(f"Simple identity format requires also setting input and output default models in Defaults (processing {spec})")
        if isinstance(spec, str):
            spec = [spec]
        ret = []
        for s in spec:
            (node, prop) = re.match("^([^.]+[.])?(.*)", s).groups()
            if node:
                node = node[:-1]
            if not node:
                if not defaults.Node:
                    raise RuntimeError(f"Node not specified in property string, with no default provided (processing {spec})")
                else:
                    node = defaults.Node
            ret.append(IOSpec(Model=defaults.Model,
                              Version=defaults.Version,
                              Node=node,
                              Props=[prop]))
        return ret

    def convert_dict_to_TfStepSpec(self, spec: dict, defaults: PackageC | None) -> TfStepSpec:
        if spec.get("Package") is None:
            if defaults is None:
                raise RuntimeError(f"Package is not defined, with no default (processing {spec}")
            spec["Package"] = defaults.model_dump()
            spec["Package"]["Name"] = spec["Package"]["Name"].replace("-","_")
            
        elif isinstance(spec["Package"], str):
            (name, version) = re.match("^([^@]+)([@].*)",
                                       spec["Package"]).groups()
            spec["Package"] = PackageC(Name=name.replace("-","_"), Version=version[1:])
        return TfStepSpec(**spec)

    def convert_string_to_TfStepSpec(self, spec: str,
                                     defaults: PackageC | None) -> TfStepSpec:
        if defaults is None:
            raise RuntimeError(f"Simple step entrypoint format also requires setting the default package in Defaults (processing {spec})")
        return TfStepSpec(Package=defaults, Entrypoint=spec)

    def parse_mdf(self) -> None:
        if not self.mdf or not self.mdf.get("TransformDefinitions"):
            self.parse_mdf_success = False
            raise RuntimeError("No transforms MDF loaded")
            return self.parse_mdf_success
        tfdefns = self.mdf["TransformDefinitions"]
        if tfdefns.get("Defaults"):
            if tfdefns["Defaults"].get("Package"):
                s = tfdefns["Defaults"]["Package"]
                if isinstance(s, str):
                    (name, version) = re.match("^([^@]+)([@].*)", s).groups()
                    tfdefns["Defaults"]["Package"] = PackageC(Name=name, Version=version[1:])
                elif isinstance(s, dict):
                    tfdefns["Defaults"]["Package"] = PackageC(**s)
                else:
                    raise RuntimeError(f"Cannot interpret package specification (processing {s})")
            self._defaults = Defaults(**tfdefns["Defaults"])
        if tfdefns.get("Identities"):
            self.parse_identities()
        if tfdefns.get("Transforms"):
            self.parse_transforms()

    def parse_identities(self) -> None:
        identities = []
        for spec in self.mdf["TransformDefinitions"]["Identities"]:
            if isinstance(spec, dict):
                ident = IdentitySpec(
                    From=self.convert_dict_to_IOSpec(spec["From"], self._defaults.Inputs)[0],
                    To=self.convert_dict_to_IOSpec(spec["To"], self._defaults.Outputs)[0]
                )
            elif isinstance(spec, list):
                if self.input_defaults is None and self.output_defaults is None:
                    raise RuntimeError(f"Simple identity format requires also setting input and output default models (processing {spec})")
                from_to = FromToList(items=spec)
                (frm, to) = from_to.items
                frm = self.convert_string_to_IOSpec(frm, self._defaults.Inputs)[0]
                to =  self.convert_string_to_IOSpec(to, self._defaults.Outputs)[0]
                ident = IdentitySpec(From=frm, To=to)
            else:
                raise RuntimeError("Can't parse as an Identity: {spec}")
            identities.append(ident)

        for ident in identities:
            handle = f"{ident.From.Node}_{ident.From.Props[0]}_to_{ident.To.Node}_{ident.To.Props[0]}"
            self._transforms[handle] = IdentityTransform(Inputs=[ident.From],
                                                         Outputs=[ident.To])

    def parse_transforms(self):
        for (hdl, spec) in self.mdf["TransformDefinitions"]["Transforms"].items():
            inputs = []
            outputs = []
            steps = []
            for s in spec["Inputs"]:
                if isinstance(s, str):
                    inputs.append(self.convert_string_to_IOSpec(s, self._defaults.Inputs)[0])
                elif isinstance(s, dict):
                    inputs.append(self.convert_dict_to_IOSpec(s, self._defaults.Inputs)[0])
                else:
                    raise RuntimeError(f"Cannot interpret transform input specification (processing {s})")
            for s in spec["Outputs"]:
                if isinstance(s, str):
                    outputs.append(self.convert_string_to_IOSpec(s, self._defaults.Outputs)[0])
                elif isinstance(s, dict):
                    outputs.append(self.convert_dict_to_IOSpec(s, self._defaults.Outputs)[0])
                else:
                    raise RuntimeError(f"Cannot interpret transform output specification (processing {s})")
            for s in spec["Steps"]:
                if isinstance(s, dict):
                    steps.append(self.convert_dict_to_TfStepSpec(s, self._defaults.Package))
                elif isinstance(s, str):
                    steps.append(self.convert_string_to_TfStepSpec(s, self._defaults.Package))
                else:
                    raise RuntimeError(f"Cannot interpret step specification ({s})")
            self._transforms[hdl] = GeneralTransform(
                Inputs=inputs,
                Outputs=outputs,
                Steps=steps
            )


