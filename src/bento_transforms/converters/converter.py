"""
bento_transforms.converters.Converter class
This object can convert _data values_ under one Model to _data values_
under another model, according to Transform information provided as
GeneralTransform Pydantic objects. The bento-meta objects can be created by reading from an
MDB or from an MDF-Tranform YAML file (using bento_transforms.mdf.TransformReader).
"""

from __future__ import annotations
import importlib
from toolz import compose_left, curry
from functools import partial
from typing import Callable, List, Tuple
from ..mdf.pymodels import GeneralTransform
from pdb import set_trace

class Converter:
    def __init__(self):
        pass


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
    return partial(porcelain, wrapper(func=tf_func, arglist=args, outlist=outs))
            
            


