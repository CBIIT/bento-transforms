"""
bento_transforms.converters.Converter class
This object can convert _data values_ under one Model to _data values_
under another model, according to Transform information provided as
GeneralTransform Pydantic objects. The bento-meta objects can be created by reading from an
MDB or from an MDF-Tranform YAML file (using bento_transforms.mdf.TransformReader).
"""

from __future__ import annotations
import importlib
import json
from toolz import compose_left, curry
from functools import partial, reduce
from collections import Counter
from typing import Callable, List, Tuple
from ..mdf.pymodels import GeneralTransform
from ..mdf.reader import TransformReader
from pdb import set_trace


class Converter:
    def __init__(self, tmdf: TransformReader | None = None, gtfs: List[GeneralTransform] | None = None):
        self._from_model = None
        self._to_model = None
        self._tfnames_by_io = {}
        self._tfuncs = {}
        if tmdf:
            self._transforms = tmdf.transforms
        elif gtfs:
            self._transforms = gtfs
        else:
            raise RuntimeError("Converter constructor requires either MDF object or dict of GeneralTransforms")
        # create signature hash table
        for hdl in self._transforms:
            self._tfnames_by_io[
                hash_gtf_by_io(self._transforms[hdl])
            ] = hdl
        pass

    @property
    def transforms(self) -> dict:
        return self._transforms

    @property
    def from_model(self) -> str:
        if not self._from_model:
            ctr = Counter(
                [(x.Model, x.Version) for x in reduce(
                    lambda x,y:x+y, [y.Inputs for y in self.transforms.values()])]
            )
            self._from_model = ctr.most_common()[0][0]
        return self._from_model

    @property
    def to_model(self) -> str:
        if not self._to_model:
            ctr = Counter(
                [(x.Model, x.Version) for x in reduce(
                    lambda x,y:x+y, [y.Outputs for y in self.transforms.values()])]
            )
            self._to_model = ctr.most_common()[0][0]
        return self._to_model

    def tfunction(self, handle) -> Callable:
        if not self._tfuncs.get(handle):
            if not self._transforms.get(handle):
                raise RuntimeError(f"No such transform '{handle}'")
            self._tfuncs[handle] = create_transform_function(
                self._transforms[handle]
            )
        return self._tfuncs[handle]

    def convert(self, frm: str | List[str], to: str | List(str)) -> Callable:
        if isinstance(frm, str):
            frm = [frm]
        if isinstance(to, str):
            to = [to]
        idx = hash(json.dumps([sorted(frm), sorted(to)]))
        if not self._tfnames_by_io.get(idx):
            raise RuntimeError(f"No transformation available with inputs '{frm}' and outputs '{to}'")
        return self.tfunction(self._tfnames_by_io[idx])


def create_transform_function(gtf: GeneralTransform) -> Callable:
    def porcelain(func: Callable, *args, **kwargs):
        if args:
            return func(args)
        elif kwargs:
            return func(kwargs)
        else:
            return func()
        
    def wrapper(inp,
                func: Callable, arglist: List[str],
                outlist: List[str]):
        if isinstance(inp, Tuple | List):
            ret = func(*inp)
        elif isinstance(inp, dict):
            if not {k for k in inp} <= {a for a in arglist}:
                raise RuntimeError("Invalid input. "
                                   f"Valid input keys are '{arglist}'")
            # this creates a list of args in the correct order
            rrgs = [inp[a] for a in arglist if a in inp]
            ret = func(*rrgs)
        else:
            ret = func(*[inp])
        if isinstance(ret, list):
            # return dict
            return {x: y for (x, y) in zip(outlist, ret)}
        else:
            # return value
            return ret

    args = []
    for inp in gtf.Inputs:
        for prop in inp.Props:
            args.append(inp.Node+"_"+prop)
    outs = []
    for outp in gtf.Outputs:
        for prop in outp.Props:
            outs.append(outp.Node+"_"+prop)
    tf_func = None
    funcs = []
    for step in gtf.Steps:
        mod = step.Package.Name
        if (mod == "Identity"):
            funcs.append(lambda x:x)
            continue
        ep = step.Entrypoint.split(".")
        mth = ep.pop()
        if len(ep) > 0:
            mod = ".".join([mod]+ep)
        module = importlib.import_module(mod)
        if hasattr(module, mth):
            method = getattr(module, mth)
        else:
            raise RuntimeError(f"Module {mod} has no method '{mth}'")
        if step.Params is not None:
            method = curry(method)
            method = method(params=step.Params)
            if not isinstance(method, Callable):
                RuntimeError("Didn't get a function back from a curried function; check the transformation implementation")
        funcs.append(method)
    if len(funcs) == 1:
        tf_func = funcs.pop()
    else:
        tf_func = compose_left(*funcs)

    wrapper = curry(wrapper)
    tf = partial(porcelain, wrapper(func=tf_func, arglist=args, outlist=outs))
    tf.__setattr__("inputs", gtf.Inputs)
    tf.__setattr__("outputs", gtf.Outputs)
    return tf


def hash_gtf_by_io(gtf: GeneralTransform) -> int:
    inp = []
    out = []
    for item in gtf.Inputs:
        node = item.Node
        for p in item.Props:
            inp.append(f"{node}.{p}")
    for item in gtf.Outputs:
        node = item.Node
        for p in item.Props:
            out.append(f"{node}.{p}")
    inp.sort()
    out.sort()
    return hash(json.dumps([inp, out]))
    
