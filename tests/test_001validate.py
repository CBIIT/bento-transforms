import pytest
from pathlib import Path
from bento_mdf.validator import MDFValidator
from bento_transforms.mdf import TransformReader

tdir = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()
test_transform_file = tdir / "samples" / "transforms.yaml"
test_mdfschema_file = tdir / "samples" / "mdf-schema-tf.yaml"

def test_reader():
    val = MDFValidator(test_mdfschema_file, test_transform_file, raise_error=True)
    assert val.load_and_validate_schema()
    assert val.load_and_validate_yaml()
    assert val.validate_instance_with_schema()
    tmdf = TransformReader(test_transform_file,
                           handle='transforms',
                           mdf_schema=test_mdfschema_file)
    assert tmdf
