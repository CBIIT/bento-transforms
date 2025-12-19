"""
bento_transforms.graph.meta

Express GeneralTransform spec in bento-meta graph object model.
Store and retrieve transforms using MDB.
"""
from __future__ import annotations

import json
import logging
import minicypher as mc
from ..mdf.pymodels import GeneralTransform
from bento_meta.objects import Node, Property
from bento_meta.tf_objects import Transform, TfStep


class TransformModel:
    def __init__(self, gtfs=dict[GeneralTransform]):
        self._transforms = {}
        for (hdl, tf) in gtfs.items():
            self._transforms[hdl] = gtf_to_tf_graph(tf, hdl)

    @property
    def transforms(self):
        return self._transforms

                 
def gtf_to_tf_graph(gtf: GeneralTransform, handle: str) -> Transform:
    tf = Transform({"handle": handle})
    nodes = {}
    props = {}
    for inp in gtf.Inputs:
        nidx = (inp.Model, inp.Version, inp.Node)
        if nodes.get(nidx) is None:
            nodes[nidx] = Node({"handle": inp.Node,
                                "model": inp.Model,
                                "version": inp.Version})
        for p in inp.Props:
            pidx = (inp.Model, inp.Version, p)
            if props.get(pidx) is None:
                props[pidx] = Property({"handle": p,
                                        "model": inp.Model,
                                        "version": inp.Version})
            nodes[nidx].props[p] = props[pidx]
            tf.input_props[f"{nodes[nidx].handle}.{props[pidx].handle}"] = props[pidx]
    for outp in gtf.Outputs:
        nidx = (outp.Model, outp.Version, outp.Node)
        if nodes.get(nidx) is None:
            nodes[nidx] = Node({"handle": outp.Node,
                                "model": outp.Model,
                                "version": outp.Version})
        for p in outp.Props:
            pidx = (outp.Model, outp.Version, p)
            if props.get(pidx) is None:
                props[pidx] = Property({"handle": p,
                                        "model": outp.Model,
                                        "version": outp.Version})
            nodes[nidx].props[p] = props[pidx]
            tf.output_props[f"{nodes[nidx].handle}.{props[pidx].handle}"] = props[pidx]
    first_step = True
    step = None
    prev_step = None
    for s in gtf.Steps:
        step = TfStep({"package": s.Package.Name,
                       "version": s.Package.Version,
                       "entrypoint": s.Entrypoint})
        if s.Params is not None:
            step.params_json = json.dumps(s.Params)
        if first_step:
            tf.first_step = step
            first_step = False
        if prev_step is not None:
            prev_step.next_step = step
        prev_step = step
    tf.last_step = step
    return tf

