from argparse import ArgumentParser
import csv
import logging
import yaml

from bento_transforms.mdf import TransformReader
from bento_transforms.converters.converter import (
    create_transform_function,
    Converter,
)
from bento_transforms.utils import logger

LOG = logger.get_logger(log_name=__file__.split("/")[-1])

# logging.basicConfig(
#    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
#    datefmt="%m-%d-%Y %H-%M-%S"
# )
# LOG = logging.getLogger(__file__.split('/')[-1])


def parse_cmd_args():
    parser = ArgumentParser()

    # parser.add_argument('-t', '--tdf_filename', help="TDF file location")
    parser.add_argument("-c", "--conf_file", help="conf file", required=True)

    cmd_args = parser.parse_args()

    return cmd_args


def main(**kwargs):
    LOG.debug(f"kwargs: {kwargs}")
    tmdf = TransformReader(kwargs.get("tdf_filename"), handle="transforms")
    tf_funcs = {}
    for entry in tmdf.transforms:
        LOG.debug(f"Processing {entry} transformation")
        tf_funcs[entry] = create_transform_function(tmdf.transforms[entry])

    input_filename = kwargs.get("input_data")
    with open(input_filename, "r", encoding="utf-8") as input_file:
        input_data = []
        if input_filename.lower().endswith("csv"):
            input_data = csv.DictReader(input_file, quoting=csv.QUOTE_NONNUMERIC)
        elif input_filename.lower().endswith("yaml"):
            input_data = yaml.safe_load(input_file)
    for row in input_data:
        LOG.debug(f"Using row {row}")
        row_result = tf_funcs["test_internal_transform"](row.get("field1"))
        LOG.debug(f"Row result: {row_result}")


if __name__ == "__main__":

    main_cmd_args = parse_cmd_args()
    with open(main_cmd_args.conf_file, "r", encoding="utf-8") as conf_file:
        conf_data = yaml.safe_load(conf_file)

    log_lvl = conf_data.get("log_lvl", "INFO")
    log_lvl = (
        log_lvl
        if log_lvl in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
        else "INFO"
    )
    logger.set_global_log_level(log_level=log_lvl)
    LOG.setLevel(log_lvl)
    LOG.info(f"Log level set to {log_lvl}")

    main(**conf_data)
