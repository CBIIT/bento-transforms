import minicypher as mc
from toolz import first, last
from itertools import pairwise
from bento_meta.mdb import make_nanoid
from bento_meta.objects import Node, Property
from bento_meta.tf_objects import Transform, TfStep


def create_tf_and_steps(tf: Transform):
    stmts = []
    tfn_id = make_nanoid()
    tfn = mc.N(label="transform",
               props=[mc.P(handle="handle", value=tf.handle),
                      mc.P(handle="nanoid", value=tfn_id)])
    stepns = {}
    stp = tf.first_step
    while stp is not None:
        stpn_id = make_nanoid()
        stepns[stpn_id] = mc.N(label="tf_step",
                               props=[mc.P(handle="package", value=stp.package),
                                      mc.P(handle="version", value=stp.version),
                                      mc.P(handle="entrypoint", value=stp.entrypoint),
                                      mc.P(handle="params_json", value=stp.params_json),
                                      mc.P(handle="nanoid", value=stpn_id)]
                               )
        stp = stp.next_step
    # merge nodes
    svals = list(stepns.values())
    stmts.append(
        mc.Statement(mc.Merge(tfn))
    )
    for stpn in svals:
        stmts.append(
            mc.Statement(mc.Merge(stpn))
        )
    # link nodes
    stmts.extend([
        mc.Statement(
            mc.Match(tfn, first(svals)),
            mc.Merge(mc.R(Type="first_step").relate(tfn.var(), first(svals).var()))
        ),
        mc.Statement(
            mc.Match(tfn, last(svals)),
            mc.Merge(mc.R(Type="last_step").relate(tfn.var(), last(svals).var()))
        ),
    ])
    for (a_stepn, b_stepn) in pairwise(svals):
        stmts.append(
            mc.Statement(
                mc.Match(a_stepn, b_stepn),
                mc.Merge(mc.R(Type="next_step").relate(a_stepn.var(), b_stepn.var()))
            )
        )
    return stmts
    

def t_from_property(prop: Property):
    # find node
    node = [e for e in prop.belongs.values() if isinstance(e, Node)]
    node = node[0]
    n = mc.N(label="node",
             props=[mc.P(handle="model", value=node.model),
                    mc.P(handle="version", value=node.version),
                    mc.P(handle="handle", value=node.handle)])
    p = mc.N(label="property",
             props=[mc.P(handle="model", value=prop.model),
                    mc.P(handle="version", value=prop.version),
                    mc.P(handle="handle", value=prop.handle)])
    r = mc.R(Type="has_property")
    return r.relate(n, p)
