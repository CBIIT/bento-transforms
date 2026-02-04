"""
bento_transforms.graph.meta

Express GeneralTransform spec in bento-meta graph object model.
Store and retrieve transforms using MDB.
"""
from __future__ import annotations

import json
import logging
from typing import Any, List
from ..mdf.pymodels import GeneralTransform, IOSpec, TfStepSpec, PackageC
from .mc_utils import (
    create_tf_and_steps,
    link_tf_to_io
)

from bento_meta.objects import Node, Property
from bento_meta.tf_objects import Transform, TfStep
from bento_meta.mdb import MDB

_GET_TRANSFORMS_QRY = (
    "match (ni:node)-[:has_property]->(pi:property)-[:value_as_tf_input]->"
    "(t:transform)-[:tf_output_as_value]->"
    "(po:property)<-[:has_property]-(no:node) "
    "with {node:ni,prop:pi} as npi, {node:no, prop:po} as npo, t "
    "with collect(npi) as npi_list, collect(npo) as npo_list, t "
    "match (ls:tf_step)<-[:last_tf_step]-(t)-[:first_tf_step]->(fs:tf_step) "
    "optional match p = (fs)-[:next_tf_step*]->(ls) "
    "return t, npi_list as inputs, npo_list as outputs, fs as first_step, nodes(p) as steps"
)


class TransformModel:
    def __init__(self, gtfs: dict[str, GeneralTransform] | None = None,
                 mdb: MDB | None = None):
        self.mdb = mdb
        self._transforms = {}
        if gtfs is not None:
            for (hdl, tf) in gtfs.items():
                self._transforms[hdl] = gtf_to_tf_graph(tf, hdl)

    @property
    def transforms(self):
        return self._transforms

    def retrieve_transforms(self) -> None:
        """Retrieve transform subgraphs from MDB and store as GeneralTransform objects."""
        if self.mdb is None:
            raise RuntimeError(
                "No MDB connection. Provide mdb= to TransformModel constructor."
            )
        records = self.mdb.get_with_statement(_GET_TRANSFORMS_QRY)
        if records is None:
            self._transforms = {}
            return
        self._transforms = records_to_gtfs(records)

    def cypher_for_upsert(self) -> List[str]:
        stmts = []
        for tf in self.transforms.values():
            ss = create_tf_and_steps(tf)
            stmts.extend(ss['stmts'])
            stmts.extend(
                link_tf_to_io(ss['tf_nanoid'], tf)
            )
        return stmts
                 

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


def records_to_gtfs(records: list[dict[str, Any]]) -> dict[str, GeneralTransform]:
    """Convert Neo4j query result records into a dict of GeneralTransform objects.

    Each record is expected to have keys matching the get_transforms.cypher RETURN clause:
      - 't': transform node (must have 'handle')
      - 'inputs': list of {node: <node_dict>, prop: <prop_dict>}
      - 'outputs': list of {node: <node_dict>, prop: <prop_dict>}
      - 'first_step': the first tf_step node dict
      - 'steps': ordered list of tf_step nodes from path, or None if single step
    """
    gtfs = {}
    for rec in records:
        handle = rec['t']['handle']

        # If steps is null (single-step transform), fall back to [first_step]
        step_records = rec['steps'] if rec['steps'] is not None else [rec['first_step']]

        inputs = _io_records_to_iospecs(rec.get('inputs', []))
        outputs = _io_records_to_iospecs(rec.get('outputs', []))

        steps = []
        for s in step_records:
            pkg = PackageC(Name=s['package'], Version=s.get('version'))
            params = None
            if s.get('params_json'):
                params = json.loads(s['params_json'])
            steps.append(TfStepSpec(
                Package=pkg,
                Entrypoint=s['entrypoint'],
                Params=params,
            ))

        gtfs[handle] = GeneralTransform(
            Inputs=inputs,
            Outputs=outputs,
            Steps=steps,
        )
    return gtfs


def _io_records_to_iospecs(io_records: list[dict]) -> list[IOSpec]:
    """Group node/prop record pairs into IOSpec objects.

    Groups properties by their parent (model, version, node) tuple.
    """
    grouped: dict[tuple, list[str]] = {}
    for item in io_records:
        node = item.get('node')
        prop = item.get('prop')
        if node is None or prop is None:
            continue
        key = (node['model'], node['version'], node['handle'])
        if key not in grouped:
            grouped[key] = []
        prop_handle = prop['handle']
        if prop_handle not in grouped[key]:
            grouped[key].append(prop_handle)

    return [
        IOSpec(Model=model, Version=version, Node=node_handle, Props=props)
        for (model, version, node_handle), props in grouped.items()
    ]
