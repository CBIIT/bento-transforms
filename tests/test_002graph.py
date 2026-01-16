import pytest
from bento_transforms.mdf import TransformReader
from bento_transforms.graph.meta import TransformModel
from bento_meta.objects import Node, Property, Tag
from bento_meta.tf_objects import Transform, TfStep

def test_meta_graph(samplesd):
    meta_tfs = {}
    tmdf = TransformReader(samplesd / "transforms.yaml", handle='transforms')
    tmdl = TransformModel(tmdf.transforms)
    assert tmdl
    
    mtf = tmdl.transforms["fullname_to_fmlnames"]

    assert isinstance(mtf, Transform)
    assert len(mtf.input_props) == 1
    assert len(mtf.output_props) == 3
    assert isinstance(mtf.first_step, TfStep)
    assert isinstance(mtf.last_step, TfStep)

    mstep = mtf.first_step
    assert mstep.entrypoint == "string.split"
    assert mstep.package == "bento_transforms"
    assert mstep.version == "0.1.1"
    assert mstep.params['delimiter'] == " "

    # Transform can haz Tags
    tag = Tag({"key": "Source", "value":"SB2"})
    mtf.tags[tag.key] = tag
    
