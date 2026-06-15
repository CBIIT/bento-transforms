from dateutil.parser import parse as du_parse
from enum import Enum

from bento_transforms.utils import logger

LOG = logger.get_logger(log_name=__file__.split("/")[-1])


# Note, this probably should live somewhere else
class DatetimeFormats(Enum):
    """The lookup here is for a set to strftime formatting"""

    MMDDYYYY_SLASH = {"format_str": "%m/%d/%Y"}
    YYMMDD_SLASH = {"format_str": "%Y/%m/%d"}
    ISOFORMAT = {"dt_function": "isoformat"}


def convert_datetime(input_datetime: str, tgt_format=None):

    new_datetime = None
    try:
        canonical_dt = du_parse(input_datetime)
    except Exception as excpt:
        LOG.error(f"Unable to convert {input_datetime}: {excpt}")
        raise excpt
    else:
        if "format_str" in tgt_format.value:
            new_datetime = canonical_dt.strftime(tgt_format.value["format_str"])
        else:
            new_datetime = getattr(canonical_dt, tgt_format.value["dt_function"])()

    return new_datetime
