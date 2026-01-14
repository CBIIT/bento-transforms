import pytest
from bento_mdf.validator import MDFValidator
from bento_transforms.mdf import TransformReader
from bento_transforms.mdf.pymodels import GeneralTransform
from pdb import set_trace


def test_reader(samplesd):
    val = MDFValidator(samplesd / "transforms.yaml",
                       samplesd / "mdf-schema-tf.yaml", raise_error=True)
    assert val.load_and_validate_schema()
    assert val.load_and_validate_yaml()
    assert val.validate_instance_with_schema()
    tmdf = TransformReader(samplesd / "transforms.yaml",
                           handle='transforms',
                           mdf_schema=samplesd / "mdf-schema-tf.yaml")
    assert tmdf
    assert tmdf.mdf['TransformDefinitions']
    assert tmdf.mdf_schema['$id']
    assert len(tmdf.transforms) == 14
    for t in tmdf._transforms.values():
        assert isinstance(t, GeneralTransform)
    tf = tmdf.transforms['age_days_to_years']
    assert tf.Steps[0].Params["divisor"] == 365
    assert tf.Steps[1].Params is None


def test_err_transforms_should_allow_identical_input_output(samplesd):
    tmdf = TransformReader(samplesd / "tdp.yaml",
                           handle="transforms",
                           mdf_schema=samplesd / "mdf-schema-tf.yaml")
    
    assert tmdf
    

def test_err_missing_default_in_From(samplesd):
    with pytest.raises(RuntimeError, match="Version not specified"):
        TransformReader(samplesd / "err_1.yaml",
                        handle='transforms',
                        mdf_schema=samplesd / "mdf-schema-tf.yaml")


def test_err_missing_default_in_To(samplesd):
    with pytest.raises(RuntimeError, match="Version not specified"):
        TransformReader(samplesd / "err_2.yaml",
                        handle='transforms',
                        mdf_schema=samplesd / "mdf-schema-tf.yaml")


def test_node_default_works_in_from(samplesd):
    assert TransformReader(samplesd / "good_3.yaml",
                           handle='transforms',
                           mdf_schema=samplesd / "mdf-schema-tf.yaml")


def test_err_missing_node_default_in_to(samplesd):
    with pytest.raises(RuntimeError, match="Node not specified"):
        TransformReader(samplesd / "err_4.yaml",
                        handle='transforms',
                        mdf_schema=samplesd / "mdf-schema-tf.yaml")


def test_err_missing_package_default_in_step(samplesd):
    with pytest.raises(RuntimeError, match="Simple step entrypoint format"):
        TransformReader(samplesd / "err_5.yaml",
                        handle='transforms',
                        mdf_schema=samplesd / "mdf-schema-tf.yaml")

