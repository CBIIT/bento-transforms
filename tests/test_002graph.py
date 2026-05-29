import pytest
from bento_transforms.mdf import TransformReader
from bento_transforms.graph.meta import (
    TransformModel,
    _io_records_to_iospecs,
    _parse_node_prop,
    _parse_package,
)    
from bento_meta.objects import Node, Property, Tag
from bento_meta.tf_objects import Transform, TfStep
from bento_transforms.mdf.pymodels import GeneralTransform, IOSpec, PackageC

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
    
# --- Tests for add_transform ---

def test_add_transform_identity_with_defaults():
    """Identity transform using instance defaults."""
    tmdl = TransformModel(
        from_model="CCDI", from_version="3.1.0",
        to_model="CDS", to_version="10.0.0",
    )
    handle = tmdl.add_transform("sample.sample_id", "specimen.specimen_id")

    assert handle == "sample_sample_id_to_specimen_specimen_id"
    gtf = tmdl.transforms[handle]
    assert isinstance(gtf, GeneralTransform)

    # Check inputs
    assert len(gtf.Inputs) == 1
    assert gtf.Inputs[0].Model == "CCDI"
    assert gtf.Inputs[0].Version == "3.1.0"
    assert gtf.Inputs[0].Node == "sample"
    assert gtf.Inputs[0].Props == ["sample_id"]

    # Check outputs
    assert len(gtf.Outputs) == 1
    assert gtf.Outputs[0].Model == "CDS"
    assert gtf.Outputs[0].Version == "10.0.0"
    assert gtf.Outputs[0].Node == "specimen"
    assert gtf.Outputs[0].Props == ["specimen_id"]

    # Check identity step
    assert len(gtf.Steps) == 1
    assert gtf.Steps[0].Package.Name == "Identity"
    assert gtf.Steps[0].Entrypoint == "identity"


def test_add_transform_with_explicit_handle():
    """Provide explicit handle."""
    tmdl = TransformModel(
        from_model="A", from_version="1.0",
        to_model="B", to_version="2.0",
    )
    handle = tmdl.add_transform(
        "node1.prop1", "node2.prop2",
        handle="my_custom_handle"
    )
    assert handle == "my_custom_handle"
    assert "my_custom_handle" in tmdl.transforms


def test_add_transform_with_steps():
    """Transform with explicit steps and package."""
    tmdl = TransformModel(
        from_model="CCDI", from_version="3.1.0",
        to_model="CDS", to_version="10.0.0",
    )
    handle = tmdl.add_transform(
        "study_personnel.personnel_name",
        "investigator.first_name",
        steps=["string.split", "string.normalize_case"],
        package="bento_transforms@0.1.1",
    )

    gtf = tmdl.transforms[handle]
    assert len(gtf.Steps) == 2
    assert gtf.Steps[0].Entrypoint == "string.split"
    assert gtf.Steps[0].Package.Name == "bento_transforms"
    assert gtf.Steps[0].Package.Version == "0.1.1"
    assert gtf.Steps[1].Entrypoint == "string.normalize_case"


def test_add_transform_with_default_package():
    """Transform using instance default_package."""
    tmdl = TransformModel(
        from_model="A", from_version="1.0",
        to_model="B", to_version="2.0",
        default_package="my_pkg@1.0.0",
    )
    handle = tmdl.add_transform(
        "n1.p1", "n2.p2",
        steps=["module.func"],
    )
    gtf = tmdl.transforms[handle]
    assert gtf.Steps[0].Package.Name == "my_pkg"
    assert gtf.Steps[0].Package.Version == "1.0.0"


def test_add_transform_override_model():
    """Override instance model defaults with explicit args."""
    tmdl = TransformModel(
        from_model="DEFAULT_FROM", from_version="0.0",
        to_model="DEFAULT_TO", to_version="0.0",
    )
    handle = tmdl.add_transform(
        "n1.p1", "n2.p2",
        from_model="OVERRIDE_FROM", from_version="1.0",
        to_model="OVERRIDE_TO", to_version="2.0",
    )
    gtf = tmdl.transforms[handle]
    assert gtf.Inputs[0].Model == "OVERRIDE_FROM"
    assert gtf.Inputs[0].Version == "1.0"
    assert gtf.Outputs[0].Model == "OVERRIDE_TO"
    assert gtf.Outputs[0].Version == "2.0"


def test_add_transform_missing_from_model():
    """Raise error when input model/version missing."""
    tmdl = TransformModel(to_model="B", to_version="2.0")
    with pytest.raises(ValueError, match="Input model and version required"):
        tmdl.add_transform("n1.p1", "n2.p2")


def test_add_transform_missing_to_model():
    """Raise error when output model/version missing."""
    tmdl = TransformModel(from_model="A", from_version="1.0")
    with pytest.raises(ValueError, match="Output model and version required"):
        tmdl.add_transform("n1.p1", "n2.p2")


def test_add_transform_missing_package_for_steps():
    """Raise error when steps provided but no package."""
    tmdl = TransformModel(
        from_model="A", from_version="1.0",
        to_model="B", to_version="2.0",
    )
    with pytest.raises(ValueError, match="Package required"):
        tmdl.add_transform("n1.p1", "n2.p2", steps=["module.func"])


# --- Tests for helper functions ---

def test_parse_node_prop():
    assert _parse_node_prop("sample.sample_id") == ("sample", "sample_id")
    assert _parse_node_prop("study_personnel.personnel_name") == ("study_personnel", "personnel_name")


def test_parse_node_prop_invalid():
    with pytest.raises(ValueError, match="Invalid format"):
        _parse_node_prop("noproperty")


def test_parse_package_with_version():
    pkg = _parse_package("bento_transforms@0.1.1")
    assert pkg.Name == "bento_transforms"
    assert pkg.Version == "0.1.1"

def test_parse_package_without_version():
    pkg = _parse_package("my_package")
    assert pkg.Name == "my_package"
    assert pkg.Version is None
