from __future__ import annotations
from typing import List
from pymodels import UuidNS, UuidNSEnum
import uuid


def generate_uuid(input: str | List[str],
                  params: UuidNS):
    """
    Args:
        values: list/tuple of values to seed UUID
        params.namespace: namespace enum member for uuid.uuid5 
    Returns:
        UUID string
    """
    if not isinstance(input, (list, tuple)):
        input = [input]

    # Map enum  to uuid constants
    ns_map = {
        UuidNSEnum.DNS: uuid.NAMESPACE_URL,
        UuidNSEnum.URL: uuid.NAMESPACE_URL,
        UuidNSEnum.OID: uuid.NAMESPACE_OID,
        UuidNSEnum.X500: uuid.NAMESPACE_X500
    }

    namespace_obj = ns_map.get(params.namespace, uuid.NAMESPACE_DNS)
    seed = "_".join(str(v) for v in input if v is not None)
    return str(uuid.uuid5(namespace_obj, seed))
