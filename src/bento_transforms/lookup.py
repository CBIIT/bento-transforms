from __future__ import annotations
import typing

def race_ccdi_to_cds(value, default="Unknown"):
    """
    Args:
        value: CCDI race value
        default: value to return if no mapping found
    Returns:
        CDS-compliant race value
    """
    mapping = {
        "African American": "Black or African American",
        "European": "White",
        "Asian": "Asian",
        "Native American": "American Indian or Alaska Native",
        "Pacific Islander": "Native Hawaiian or Other Pacific Islander",
        "Other": "Other",
        "Unknown": "Unknown",
        "Not Reported": "Unknown"
    }
    return mapping.get(value, default)

def race_cds_to_ccdi(value, default="Unknown"):
    """Reverse mapping; note some CDS values map to 'Other' in CCDI"""
    mapping = {
        "Black or African American": "African American",
        "White": "European",
        "Asian": "Asian",
        "American Indian or Alaska Native": "Native American",
        "Native Hawaiian or Other Pacific Islander": "Pacific Islander",
        "Other": "Other",
        "Unknown": "Unknown"
    }
    return mapping.get(value, default)
