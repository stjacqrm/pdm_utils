"""Use this script to run all pipelines within the pipelines folder.
It verifies a valid pipeline is selected,
then passes all command line arguments to the main pipeline module.
"""
import argparse
import sys

from pdm_utils.pipelines.cdd import cdd
from pdm_utils.pipelines.data_retrieval import retrieve_data
from pdm_utils.pipelines.db_compare import compare_databases
from pdm_utils.pipelines.db_export import export_database
from pdm_utils.pipelines.db_freeze import freeze_database
from pdm_utils.pipelines.db_import import import_genome
from pdm_utils.pipelines.db_import import import_phage
from pdm_utils.pipelines.phamerate import phamerate
from pdm_utils.pipelines.db_export import file_export, push_db
from pdm_utils.pipelines.db_update import update_field, get_db


def main(unparsed_args):
    """Verify a valid pipeline is selected and arguments provided are valid.

    The command line arguments are parsed and performs several basic
    checks on the arguments. Then they are passed to sub-functions to
    specifically validate the arguments based on the selected pipeline.
    """
    RUN_HELP = "Command line script to call a pdm_utils pipeline."
    USAGE = "python3 -m pdm_utils [pipeline]"
    VALID_PIPELINES = {
        "get_db",
        "get_data",
        "update",
        "import",
        "import_dev",
        "cdd",
        "phamerate",
        "export",
        "file_export",
        "freeze",
        "compare",
        "push"}
    PIPELINE_HELP = "Name of the pdm_utils pipeline to run."
    pipe_parser = argparse.ArgumentParser(description=RUN_HELP, usage=USAGE)
    pipe_parser.add_argument("pipeline", type=str,
        choices=list(VALID_PIPELINES), help=PIPELINE_HELP)

    # Assumed command line arg structure:
    # python3 -m pdm_utils.run <pipeline> <additional args...>
    # sys.argv:      [0]            [1]         [2...]
    args = pipe_parser.parse_args(unparsed_args[1:2])
    if args.pipeline == "get_data":
        retrieve_data.main(unparsed_args)
    # Note: import_phage is the legacy import script and will be deprecated.
    # Once import_genome is tested and operational, 'import' will call the
    # 'import_genome' module instead of the 'import_phage' module.
    elif args.pipeline == "get_db":
        get_db.main(unparsed_args)
    elif args.pipeline == "update":
        update_field.main(unparsed_args[unparsed_args.index("update") + 1:])
    elif args.pipeline == "import":
        import_phage.main(unparsed_args)
    elif args.pipeline == "import_dev":
        import_genome.main(unparsed_args)
    elif args.pipeline == "cdd":
        cdd.main(unparsed_args[unparsed_args.index("cdd") + 1:])
    elif args.pipeline == "phamerate":
        phamerate.main(unparsed_args[unparsed_args.index("phamerate") + 1:])
    elif args.pipeline == "export":
        export_database.main(unparsed_args)
    # TODO eventually 'database_to_file' will be merged into 'export' pipeline.
    elif args.pipeline == "file_export":
        file_export.main(unparsed_args)
    elif args.pipeline == "push":
        push_db.main(unparsed_args)
    elif args.pipeline == "freeze":
        freeze_database.main(unparsed_args)
    else:
        compare_databases.main(unparsed_args)
    print("Pipeline completed")
