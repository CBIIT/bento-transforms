import pytest
from unittest.mock import MagicMock
from bento_transforms.graph.meta import (
    TransformModel,
    records_to_gtfs,
    _io_records_to_iospecs,
)
from bento_transforms.mdf.pymodels import GeneralTransform, IOSpec, PackageC


def test_records_to_gtfs_multi_step():
    records = [
        {
            't': {'handle': 'fullname_to_fmlnames'},
            'first_step': {
                'package': 'bento_transforms',
                'version': '0.1.1',
                'entrypoint': 'string.split',
                'params_json': '{"delimiter": " "}',
            },
            'steps': [
                {
                    'package': 'bento_transforms',
                    'version': '0.1.1',
                    'entrypoint': 'string.split',
                    'params_json': '{"delimiter": " "}',
                },
                {
                    'package': 'bento_transforms',
                    'version': '0.1.1',
                    'entrypoint': 'string.normalize_case',
                    'params_json': None,
                },
            ],
            'inputs': [
                {
                    'node': {'handle': 'study_personnel', 'model': 'CCDI', 'version': '3.1.0'},
                    'prop': {'handle': 'personnel_name', 'model': 'CCDI', 'version': '3.1.0'},
                },
            ],
            'outputs': [
                {
                    'node': {'handle': 'investigator', 'model': 'CDS', 'version': '10.0.0'},
                    'prop': {'handle': 'first_name', 'model': 'CDS', 'version': '10.0.0'},
                },
                {
                    'node': {'handle': 'investigator', 'model': 'CDS', 'version': '10.0.0'},
                    'prop': {'handle': 'last_name', 'model': 'CDS', 'version': '10.0.0'},
                },
            ],
        }
    ]
    result = records_to_gtfs(records)
    assert 'fullname_to_fmlnames' in result
    gtf = result['fullname_to_fmlnames']
    assert isinstance(gtf, GeneralTransform)

    # Steps
    assert len(gtf.Steps) == 2
    assert gtf.Steps[0].Entrypoint == 'string.split'
    assert gtf.Steps[0].Params == {"delimiter": " "}
    assert gtf.Steps[0].Package.Name == 'bento_transforms'
    assert gtf.Steps[1].Entrypoint == 'string.normalize_case'
    assert gtf.Steps[1].Params is None

    # Inputs
    assert len(gtf.Inputs) == 1
    assert gtf.Inputs[0].Model == 'CCDI'
    assert gtf.Inputs[0].Node == 'study_personnel'
    assert gtf.Inputs[0].Props == ['personnel_name']

    # Outputs grouped into single IOSpec
    assert len(gtf.Outputs) == 1
    assert gtf.Outputs[0].Node == 'investigator'
    assert 'first_name' in gtf.Outputs[0].Props
    assert 'last_name' in gtf.Outputs[0].Props


def test_records_to_gtfs_single_step_fallback():
    """When steps is None (single-step transform), fall back to [first_step]."""
    records = [
        {
            't': {'handle': 'identity_tf'},
            'first_step': {
                'package': 'bento_transforms',
                'version': '0.1.0',
                'entrypoint': 'basic.identity',
                'params_json': None,
            },
            'steps': None,
            'inputs': [
                {
                    'node': {'handle': 'sample', 'model': 'CCDI', 'version': '3.1.0'},
                    'prop': {'handle': 'sample_id', 'model': 'CCDI', 'version': '3.1.0'},
                },
            ],
            'outputs': [
                {
                    'node': {'handle': 'specimen', 'model': 'CDS', 'version': '10.0.0'},
                    'prop': {'handle': 'specimen_id', 'model': 'CDS', 'version': '10.0.0'},
                },
            ],
        }
    ]
    result = records_to_gtfs(records)
    gtf = result['identity_tf']
    assert len(gtf.Steps) == 1
    assert gtf.Steps[0].Entrypoint == 'basic.identity'
    assert gtf.Steps[0].Params is None


def test_records_to_gtfs_params_json_dict():
    records = [
        {
            't': {'handle': 'days_tf'},
            'first_step': {
                'package': 'bento_transforms',
                'version': '0.1.0',
                'entrypoint': 'arith.days_to_years',
                'params_json': '{"divisor": 365.25, "precision": 2}',
            },
            'steps': None,
            'inputs': [
                {
                    'node': {'handle': 'diagnosis', 'model': 'A', 'version': '1.0'},
                    'prop': {'handle': 'age_days', 'model': 'A', 'version': '1.0'},
                },
            ],
            'outputs': [
                {
                    'node': {'handle': 'diagnosis', 'model': 'B', 'version': '2.0'},
                    'prop': {'handle': 'age_years', 'model': 'B', 'version': '2.0'},
                },
            ],
        }
    ]
    result = records_to_gtfs(records)
    gtf = result['days_tf']
    assert gtf.Steps[0].Params == {"divisor": 365.25, "precision": 2}


def test_records_to_gtfs_empty():
    assert records_to_gtfs([]) == {}


def test_io_records_to_iospecs_grouping():
    """Multiple props on the same node should be grouped into one IOSpec."""
    io_records = [
        {
            'node': {'handle': 'investigator', 'model': 'CDS', 'version': '10.0.0'},
            'prop': {'handle': 'first_name', 'model': 'CDS', 'version': '10.0.0'},
        },
        {
            'node': {'handle': 'investigator', 'model': 'CDS', 'version': '10.0.0'},
            'prop': {'handle': 'middle_name', 'model': 'CDS', 'version': '10.0.0'},
        },
        {
            'node': {'handle': 'investigator', 'model': 'CDS', 'version': '10.0.0'},
            'prop': {'handle': 'last_name', 'model': 'CDS', 'version': '10.0.0'},
        },
    ]
    result = _io_records_to_iospecs(io_records)
    assert len(result) == 1
    assert result[0].Node == 'investigator'
    assert len(result[0].Props) == 3


def test_io_records_to_iospecs_skips_none():
    io_records = [
        {'node': None, 'prop': {'handle': 'x', 'model': 'A', 'version': '1'}},
        {'node': {'handle': 'n', 'model': 'A', 'version': '1'}, 'prop': None},
    ]
    result = _io_records_to_iospecs(io_records)
    assert result == []


def test_io_records_to_iospecs_dedup_props():
    """Duplicate prop handles should not appear twice."""
    io_records = [
        {
            'node': {'handle': 'n', 'model': 'A', 'version': '1'},
            'prop': {'handle': 'p1', 'model': 'A', 'version': '1'},
        },
        {
            'node': {'handle': 'n', 'model': 'A', 'version': '1'},
            'prop': {'handle': 'p1', 'model': 'A', 'version': '1'},
        },
    ]
    result = _io_records_to_iospecs(io_records)
    assert len(result) == 1
    assert result[0].Props == ['p1']


def test_constructor_with_mdb():
    mock_mdb = MagicMock()
    tmdl = TransformModel(mdb=mock_mdb)
    assert tmdl.mdb is mock_mdb
    assert tmdl.transforms == {}


def test_constructor_no_args():
    tmdl = TransformModel()
    assert tmdl.transforms == {}
    assert tmdl.mdb is None


def test_retrieve_transforms_no_mdb():
    tmdl = TransformModel()
    with pytest.raises(RuntimeError, match="No MDB connection"):
        tmdl.retrieve_transforms()


