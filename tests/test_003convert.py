import pytest
from bento_transforms.mdf import TransformReader
from bento_transforms.converters.converter import (
    create_transform_function,
    Converter,
)
from typing import Callable
from pdb import set_trace


def test_tf_functions(samplesd):
    tmdf = TransformReader(samplesd / "tf_func_test.yaml",
                           handle='transforms',
                           mdf_schema=samplesd / "mdf-schema-tf.yaml")
    tf_func = create_transform_function(
        tmdf.transforms['fullname_to_fmlnames']
    )
    assert isinstance(tf_func, Callable)

    ret = tf_func("Sigismund Leonhart Popbutton")
    assert tf_func.inputs[0].Node == "study_personnel"
    assert tf_func.outputs[0].Props == ["first_name", "middle_name",
                                        "last_name"]
    assert len(ret) == 3

    ret = tf_func(study_personnel_personnel_name="Sigismund Leonhart Popbutton")
    assert ret['investigator_middle_name'] == "Leonhart"

    with pytest.raises(RuntimeError, match="Valid input keys are"):
        tf_func(**{"squidward": "Sigismund Leonhart Popbutton"})

    # identity
    tf_func = create_transform_function(
        tmdf.transforms[
            "study_personnel_email_address_to_investigator_email"
        ]
    )

    assert tf_func("boog") == "boog"

    # multistep
    tf_func = create_transform_function(
        tmdf.transforms["lookup_and_prefix"]
    )
    assert tf_func("Native American") == "GC:American Indian or Alaska Native"


def test_converter(samplesd):
    tmdf = TransformReader(samplesd / "tf_func_test.yaml",
                           handle='transforms',
                           mdf_schema=samplesd / "mdf-schema-tf.yaml")
    cvtr = Converter(tmdf=tmdf)
    assert cvtr

    assert cvtr.from_model == ('CCDI', '3.1.0')
    assert cvtr.to_model == ('CDS', '10.0.0')

    assert isinstance(cvtr.tfunction('fullname_to_fmlnames'), Callable)
    with pytest.raises(RuntimeError, match="No such transform"):
        cvtr.tfunction("narb")
    assert isinstance(
        
        cvtr.convert(frm="study_personnel.personnel_name",
                     to=["investigator.first_name", "investigator.middle_name",
                         "investigator.last_name"]),

        Callable)

    ans = cvtr.convert(
        frm="study_personnel.personnel_name",
        to=["investigator.first_name", "investigator.middle_name",
            "investigator.last_name"])("James Earl Jones")

    assert ans["investigator_first_name"] == "James"

    assert isinstance(cvtr.convert("study_personnel.email_address",
                                   "investigator.email"),
                      Callable)
    with pytest.raises(RuntimeError, match="study_personell"):
        cvtr.convert(frm="study_personell.personnel_name",
                     to=["investigator.first_name", "investigator.middle_name",
                         "investigator.last_name"])        
