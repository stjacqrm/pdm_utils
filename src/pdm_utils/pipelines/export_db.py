"""Pipeline for exporting database information into files."""
import argparse
import csv
import os
import shutil
import sys
import time
from functools import singledispatch
from pathlib import Path
from typing import List, Dict

from Bio import SeqIO
from Bio.Alphabet import IUPAC
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord
from sqlalchemy.sql.elements import Null

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.classes.filter import Filter
from pdm_utils.functions import basic
from pdm_utils.functions import flat_files
from pdm_utils.functions import mysqldb
from pdm_utils.functions import mysqldb_basic
from pdm_utils.functions import parsing
from pdm_utils.functions import querying


#GLOBAL VARIABLES
#-----------------------------------------------------------------------------
DEFAULT_FOLDER_NAME = f"{time.strftime('%Y%m%d')}_export"
DEFAULT_FOLDER_PATH = Path.cwd()

DEFAULT_TABLE = "phage"

PHAGE_QUERY = "SELECT * FROM phage"
GENE_QUERY = "SELECT * FROM gene"

# Valid Biopython formats that crash the script due to specific values in
# some genomes that can probably be fixed relatively easily and implemented.
# BIOPYTHON_PIPELINES_FIXABLE = ["embl", "imgt", "seqxml"]
# Biopython formats that are not applicable.
# BIOPYTHON_PIPELINES_INVALID = ["fastq", "fastq-solexa", "fastq-illumina",
#                              "phd", "sff", "qual"]
# Biopython formats that are not writable
# BIOPYTHON_PIPELINES_NOT_WRITABLE = ["ig"]

# Valid file formats using Biopython
BIOPYTHON_PIPELINES = ["gb", "fasta", "clustal", "fasta-2line", "nexus",
                       "phylip", "pir", "stockholm", "tab"]
FILTERABLE_PIPELINES = BIOPYTHON_PIPELINES + ["csv"]
PIPELINES = FILTERABLE_PIPELINES + ["sql"]
FLAT_FILE_TABLES = ["phage", "gene"]

#Once trna has data, these tables can be reintroduced.
TABLES = ["phage", "gene", "domain", "gene_domain", "pham",
          #"trna", "tmrna", "trna_structures",
          "version"]
SEQUENCE_COLUMNS = {"phage"           : ["Sequence"],
                    "gene"            : ["Translation"],
                    "domain"          : [],
                    "gene_domain"     : [],
                    "pham"            : [],
                    "trna"            : ["Sequence"],
                    "tmrna"           : [],
                    "trna_structures" : [],
                    "version"         : []}

#-----------------------------------------------------------------------------
#MAIN FUNCTIONS
#-----------------------------------------------------------------------------

def main(unparsed_args_list):
    """Uses parsed args to run the entirety of the file export pipeline.

    :param unparsed_args_list: Input a list of command line args.
    :type unparsed_args_list: list[str]
    """
    #Returns after printing appropriate error message from parsing/connecting.
    args = parse_export(unparsed_args_list)

    alchemist = AlchemyHandler(database=args.database)
    alchemist.connect(ask_database=True, pipeline=True)
    alchemist.build_graph()

    # Exporting as a SQL file is not constricted by schema version.
    if args.pipeline != "sql":
        mysqldb.check_schema_compatibility(alchemist.engine, "export")

    values = []
    if args.pipeline in FILTERABLE_PIPELINES:
        values = parse_value_input(args.input)

    if not args.pipeline in PIPELINES:
        print("ABORTED EXPORT: Unknown pipeline option discrepency.\n"
              "Pipeline parsed from command line args is not supported")
        sys.exit(1)

    if args.pipeline != "I":
        execute_export(alchemist, args.folder_path, args.folder_name,
                       args.pipeline, table=args.table, values=values,
                       filters=args.filters, groups=args.groups, sort=args.sort,
                       include_columns=args.include_columns,
                       exclude_columns=args.exclude_columns,
                       sequence_columns=args.sequence_columns,
                       raw_bytes=args.raw_bytes,
                       concatenate=args.concatenate,
                       verbose=args.verbose)
    else:
        pass

def parse_export(unparsed_args_list):
    """Parses export_db arguments and stores them with an argparse object.

    :param unparsed_args_list: Input a list of command line args.
    :type unparsed_args_list: list[str]
    :returns: ArgParse module parsed args.
    """
    EXPORT_SELECT_HELP = """
        Select a export pipeline option to export database data.
            Select csv to export data from a table into a .csv file.
            Select sql to dump the current database into a .sql file.
            Select a formatted file option to export individual entries.
        """
    DATABASE_HELP = "Name of the MySQL database to export from."


    VERBOSE_HELP = """
        Export option that enables progress print statements.
        """
    FOLDER_PATH_HELP = """
        Export option to change the path
        of the directory where the exported files are stored.
            Follow selection argument with the path to the
            desired export directory.
        """
    FOLDER_NAME_HELP = """
        Export option to change the name
        of the directory where the exported files are stored.
            Follow selection argument with the desired name.
        """


    IMPORT_FILE_HELP = """
        Selection input option that imports values from a csv file.
            Follow selection argument with path to the
            csv file containing the names of each genome in the first column.
        """
    SINGLE_GENOMES_HELP = """
        Selection input option that imports values from cmd line input.
            Follow selection argument with space separated
            names of genomes in the database.
        """
    TABLE_HELP = """
        Selection option that changes the table in the database selected from.
            Follow selection argument with a valid table from the database.
        """
    WHERE_HELP = """
        Data filtering option that filters data by the inputted expressions.
            Follow selection argument with formatted filter expression:
                {Table}.{Column}={Value}
        """
    GROUP_BY_HELP = """
        Data selection option that groups data by the inputted columns.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    ORDER_BY_HELP = """
        Data selection option that sorts data by the inputted columns.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """


    CONCATENATE_HELP = """
        SeqRecord export option to toggle concatenation of files.
            Toggle to enable concatenation of files.
        """


    SEQUENCE_COLUMNS_HELP = """
        Csv export option to toggle removal of sequence-based data.
            Toggle to include sequence based data.
        """
    INCLUDE_COLUMNS_HELP = """
        Csv export option to add additional columns of a database
        to an exported csv file.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    EXCLUDE_COLUMNS_HELP = """
        Csv export option to exclude select columns of a database
        from an exported csv file.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    RAW_BYTES_HELP = """
        Csv export option to conserve blob and encoded data from the database
        when exporting to a csv file.
            Toggle to leave conserve format of bytes-type data.
        """

    initial_parser = argparse.ArgumentParser()
    initial_parser.add_argument("database", type=str, help=DATABASE_HELP)

    initial_parser.add_argument("pipeline", type=str, choices=PIPELINES,
                               help=EXPORT_SELECT_HELP)

    initial = initial_parser.parse_args(unparsed_args_list[2:4])

    optional_parser = argparse.ArgumentParser()

    optional_parser.add_argument("-m", "--folder_name",
                               type=str, help=FOLDER_NAME_HELP)
    optional_parser.add_argument("-o", "--folder_path", type=convert_dir_path,
                               help=FOLDER_PATH_HELP)
    optional_parser.add_argument("-v", "--verbose", action="store_true",
                               help=VERBOSE_HELP)


    if initial.pipeline in (BIOPYTHON_PIPELINES + ["csv"]):
        table_choices = dict.fromkeys(BIOPYTHON_PIPELINES, FLAT_FILE_TABLES)
        table_choices.update({"csv": TABLES})
        optional_parser.add_argument("-t", "--table", help=TABLE_HELP,
                                choices=table_choices[initial.pipeline])

        optional_parser.add_argument("-if", "--import_file",
                                type=convert_file_path,
                                help=IMPORT_FILE_HELP, dest="input",
                                default=[])
        optional_parser.add_argument("-in", "--import_names", nargs="*",
                                help=SINGLE_GENOMES_HELP, dest="input")
        optional_parser.add_argument("-f", "--where", nargs="?",
                                help=WHERE_HELP,
                                dest="filters")
        optional_parser.add_argument("-g", "--group_by", nargs="*",
                                help=GROUP_BY_HELP,
                                dest="groups")
        optional_parser.add_argument("-s", "--order_by", nargs="*",
                                help=ORDER_BY_HELP)

        if initial.pipeline in BIOPYTHON_PIPELINES:
            optional_parser.add_argument("-cc", "--concatenate",
                                help=CONCATENATE_HELP, action="store_true")
        else:
            optional_parser.add_argument("-sc", "--sequence_columns",
                                help=SEQUENCE_COLUMNS_HELP, action="store_true")
            optional_parser.add_argument("-ic", "--include_columns", nargs="*",
                                help=INCLUDE_COLUMNS_HELP)
            optional_parser.add_argument("-ec", "--exclude_columns", nargs="*",
                                help=EXCLUDE_COLUMNS_HELP)
            optional_parser.add_argument("-rb", "--raw_bytes",
                                help=RAW_BYTES_HELP, action="store_true")

    optional_parser.set_defaults(pipeline=initial.pipeline,
                                 database=initial.database,
                                 folder_name=DEFAULT_FOLDER_NAME,
                                 folder_path=DEFAULT_FOLDER_PATH,
                                 verbose=False, input=[],
                                 table=DEFAULT_TABLE,
                                 filters="", groups=[], sort=[],
                                 include_columns=[], exclude_columns=[],
                                 sequence_columns=False, concatenate=False,
                                 raw_bytes=False)

    parsed_args = optional_parser.parse_args(unparsed_args_list[4:])

    return parsed_args

def execute_export(alchemist, folder_path, folder_name, pipeline,
                        values=[], verbose=False, table=DEFAULT_TABLE,
                        filters="", groups=[], sort=[],
                        include_columns=[], exclude_columns=[],
                        sequence_columns=False, raw_bytes=False,
                        concatenate=False):
    """Executes the entirety of the file export pipeline.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param folder_path: Path to a valid dir for new dir creation.
    :type folder_path: Path
    :param folder_name: A name for the export folder.
    :type folder_name: str
    :param pipeline: File type that dictates data processing.
    :type pipeline: str
    :param values: List of values to filter database results.
    :type values: list[str]
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    :param table: MySQL table name.
    :type table: str
    :param filters: A list of lists with filter values, grouped by ORs.
    :type filters: list[list[str]]
    :param groups: A list of supported MySQL column names to group by.
    :type groups: list[str]
    :param sort: A list of supported MySQL column names to sort by.
    :param include_columns: A csv export column selection parameter.
    :type include_columns: list[str]
    :param exclude_columns: A csv export column selection parameter.
    :type exclude_columns: list[str]
    :param sequence_columns: A boolean to toggle inclusion of sequence data.
    :type sequence_columns: bool
    :param concatenate: A boolean to toggle concaternation for SeqRecords.
    :type concaternate: bool
    """
    if verbose:
        print("Retrieving database version...")
    db_version = mysqldb_basic.get_first_row_data(alchemist.engine, "version")

    if pipeline == "csv":
        if verbose:
            print("Processing columns for csv export...")
        csv_columns = filter_csv_columns(alchemist, table,
                                      include_columns=include_columns,
                                      exclude_columns=exclude_columns,
                                      sequence_columns=sequence_columns)

    if pipeline in FILTERABLE_PIPELINES:
        if verbose:
            print("Processing columns for sorting...")
        db_filter = apply_filters(alchemist, table, filters, verbose=verbose)

    if verbose:
        print("Creating export folder...")
    export_path = folder_path.joinpath(folder_name)
    export_path = basic.make_new_dir(folder_path, export_path, attempt=50)

    if pipeline == "sql":
        if verbose:
            print("Writing SQL database file...")
        write_database(alchemist, db_version["Version"], export_path)

    elif pipeline in FILTERABLE_PIPELINES:
        conditionals_map = {}
        build_groups_map(db_filter, export_path, conditionals_map,
                                                 groups=groups,
                                                 verbose=verbose)

        if verbose:
            print("Prepared query and path structure, beginning export...")

        for mapped_path in conditionals_map.keys():
            db_filter.reset()
            db_filter.values = values

            conditionals = conditionals_map[mapped_path]
            db_filter.values = db_filter.build_values(where=conditionals)

            if db_filter.hits() == 0:
                print(f"No database entries received from {table} "
                      f"for '{mapped_path}'.")
                continue

            if sort:
                sort_columns = get_sort_columns(alchemist, sort)
                db_filter.sort(sort_columns)

            if pipeline in BIOPYTHON_PIPELINES:
                execute_ffx_export(alchemist, mapped_path, export_path,
                                   db_filter.values, pipeline, db_version,
                                   table, concatenate=concatenate,
                                   verbose=verbose)
            else:
                execute_csv_export(db_filter, mapped_path, export_path,
                                   csv_columns, table, raw_bytes=raw_bytes,
                                   verbose=verbose)
    else:
        print("Unrecognized export pipeline, aborting export")
        sys.exit(1)

def execute_csv_export(db_filter, export_path, folder_path, columns, csv_name,
                                        sort=[], raw_bytes=False,
                                        verbose=False):
    """Executes csv export of a MySQL database table with select columns.

    :param alchemist: A connected and fully build AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param export_path: Path to a dir for file creation.
    :type export_path: Path
    :param folder_path: Path to a top-level dir.
    :type folder_path: Path
    :param table: MySQL table name.
    :type table: str
    :param conditionals: MySQL WHERE clause-related SQLAlchemy objects.
    :type conditionals: list[BinaryExpression]
    :param sort: A list of SQLAlchemy Columns to sort by.
    :type sort: list[Column]
    :param values: List of values to fitler database results.
    :type values: list[str]
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    if verbose:
        relative_path = str(export_path.relative_to(folder_path))
        print(f"Preparing {csv_name} export for '{relative_path}'...")

    headers = [db_filter._key.name]
    for column in columns:
        if column.name != db_filter._key.name:
            headers.append(column.name)

    results = db_filter.select(columns)

    if not raw_bytes:
        decode_results(results, columns, verbose=verbose)

    if len(results) == 0:
        print(f"No database entries received for {csv_name}.")
        export_path.rmdir()

    else:
        if verbose:
            print(f"...Writing csv {csv_name}.csv in '{export_path.name}'...")
            print("......Database entries retrieved: {len(results)}")

        file_path = export_path.joinpath(f"{csv_name}.csv")
        basic.export_data_dict(results, file_path, headers,
                                               include_headers=True)

def execute_ffx_export(alchemist, export_path, folder_path, values,
                       file_format, db_version, table,
                       concatenate=False, verbose=False):
    """Executes SeqRecord export of the compilation of data from a MySQL emtry.

    :param alchemist: A connected and fully build AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param export_path: Path to a dir for file creation.
    :type export_path: Path
    :param folder_path: Path to a top-level dir.
    :type folder_path: Path
    :param file_format: Biopython supported file type.
    :type file_format: str
    :param db_version: Dictionary containing database version information.
    :type db_version: dict
    :param table: MySQL table name.
    :type table: str
    :param values: List of values to fitler database results.
    :type values: list[str]
    :param conditionals: MySQL WHERE clause-related SQLAlchemy objects.
    :type conditionals: list[BinaryExpression]
    :param sort: A list of SQLAlchemy Columns to sort by.
    :type sort: list[Column]
    :param concatenate: A boolean to toggle concatenation of SeqRecords.
    :type concaternate: bool
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    if verbose:
        print(f"Retrieving {export_path.name} data...")

    if verbose:
        print(f"...Database entries retrieved: {len(values)}")
    seqrecords = []
    if table == "phage":
        seqrecords = get_genome_seqrecords(alchemist, values=values,
                                                            verbose=verbose)
    elif table == "gene":
        seqrecords = get_cds_seqrecords(alchemist, values=values,
                                                            verbose=verbose)
    else:
        print(f"Unknown error occured, table '{table}' is not recognized "
               "for SeqRecord export pipelines.")
        sys.exit(1)

    if verbose:
            print("Appending database version...")
    for record in seqrecords:
        append_database_version(record, db_version)
    write_seqrecord(seqrecords, file_format, export_path, verbose=verbose,
                                                    concatenate=concatenate)

def write_seqrecord(seqrecord_list, file_format, export_path, concatenate=False,
                                                              verbose=False):
    """Outputs files with a particuar format from a SeqRecord list.

    :param seq_record_list: List of populated SeqRecords.
    :type seq_record_list: list[SeqRecord]
    :param file_format: Biopython supported file type.
    :type file_format: str
    :param export_path: Path to a dir for file creation.
    :type export_path: Path
    :param concatenate: A boolean to toggle concatenation of SeqRecords.
    :type concaternate: bool
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    if verbose:
        print("Writing selected data to files...")

    record_dictionary = {}
    if concatenate:
        record_dictionary.update({export_path.name:seqrecord_list})
    else:
        for record in seqrecord_list:
            record_dictionary.update({record.name:record})

    for record_name in record_dictionary.keys():
        if verbose:
            print(f"...Writing {record_name}...")
        file_name = f"{record_name}.{file_format}"
        file_path = export_path.joinpath(file_name)
        file_handle = file_path.open(mode='w')
        SeqIO.write(record_dictionary[record_name], file_handle, file_format)
        file_handle.close()

def write_database(alchemist, version, export_path):
    """Output .sql file from the selected database.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param version: Database version information.
    :type version: int
    :param export_path: Path to a valid dir for file creation.
    :type export_path: Path
    """
    sql_path = export_path.joinpath(f"{alchemist.database}.sql")
    os.system(f"mysqldump -u {alchemist.username} -p{alchemist.password} "
              f"--skip-comments {alchemist.database} > {str(sql_path)}")
    version_path = sql_path.with_name(f"{alchemist.database}.version")
    version_path.touch()
    version_path.write_text(f"{version}")

#-----------------------------------------------------------------------------
#PIPELINE SETUP FUNCTIONS
#-----------------------------------------------------------------------------

def convert_dir_path(path: str):
    """Function to convert argparse input to a working directory path.

    :param path: A string to be converted into a Path object.
    :type path: str
    :returns: A Path object converted from the inputed string.
    :rtype: Path
    """
    return basic.set_path(Path(path), kind="dir")

def convert_file_path(path: str):
    """Function to convert argparse input to a working file path.

    :param path: A string to be converted into a Path object.
    :type path: str
    :returns: A Path object converted from the inputed string.
    :rtype: Path
    """
    return basic.set_path(Path(path), kind="file")

@singledispatch
def parse_value_input(value_list_input):
    """Function to convert values input to a recognized data types.

    :param value_list_input: Values stored in recognized data types.
    :type value_list_input: list[str]
    :type value_list_input: Path
    :returns: List of values to filter database results.
    :rtype: list[str]
    """

    print("Value list input for export is of an unexpected type.")
    sys.exit(1)

@parse_value_input.register(Path)
def _(value_list_input):
    value_list = []
    with open(value_list_input, newline = '') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter = ",")
        for name in csv_reader:
            value_list.append(name[0])
    return value_list

@parse_value_input.register(list)
def _(value_list_input):
    return value_list_input

#-----------------------------------------------------------------------------
#EXPORT-SPECIFIC HELPER FUNCTIONS
#-----------------------------------------------------------------------------

def get_genome_seqrecords(alchemist, values=[], verbose=False):
    genomes = mysqldb.parse_genome_data(alchemist.engine,
                                        phage_id_list=values,
                                        phage_query=PHAGE_QUERY,
                                        gene_query=GENE_QUERY)

    seqrecords = []
    for gnm in genomes:
        process_cds_features(gnm)
        if verbose:
            print(f"Converting {gnm.name}...")
        seqrecords.append(flat_files.genome_to_seqrecord(gnm))

    return seqrecords

def get_cds_seqrecords(alchemist, values=[], nucleotide=False, verbose=False):
    cds_list = parse_feature_data(alchemist, values=values)

    seqrecords = []
    genomes_dict = {}
    for cds in cds_list:
        if not cds.genome_id in genomes_dict.keys():
            if verbose:
                print(f"...Retrieving parent genome for {cds.id}...")
            phage_id_obj = querying.get_column(alchemist.metadata,
                                               "phage.PhageID")
            phage_obj = phage_id_obj.table

            parent_genome_query = querying.build_select(
                                                alchemist.graph,
                                                phage_obj,
                                                where=\
                                                phage_id_obj==cds.genome_id)
            parent_genome_data = mysqldb_basic.first(alchemist.engine,
                                                     parent_genome_query)
            parent_genome = mysqldb.parse_phage_table_data(parent_genome_data)
            genomes_dict.update({cds.genome_id : parent_genome})

        if verbose:
            print(f"Converting {cds.id}...")
        cds.genome_length = genomes_dict[cds.genome_id].length
        cds.set_seqfeature()

        record = cds_to_seqrecord(cds, genomes_dict[cds.genome_id])
        seqrecords.append(record)

    return seqrecords

def apply_filters(alchemist, table, filters, values=None,
                                                     verbose=False):
    """Applies MySQL WHERE clause filters using a Filter.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param table: MySQL table name.
    :type table: str
    :param filters: A list of lists with filter values, grouped by ORs.
    :type filters: list[list[str]]
    :param groups: A list of supported MySQL column names.
    :type groups: list[str]
    :returns: filter-Loaded Filter object.
    :rtype: Filter
    """
    db_filter = Filter(alchemist=alchemist, key=table)
    db_filter.key = table
    db_filter.values = values

    try:
        db_filter.add(filters)
    except:
        print("Please check your syntax for the conditional string: "
             f"{filters}")
        exit(1)

    return db_filter

def build_groups_map(db_filter, export_path, conditionals_map, groups=[],
                                                               verbose=False,
                                                               previous=None,
                                                               depth=0):
    """Recursive function that generates conditionals and maps them to a Path.

    :param db_filter: A connected and fully loaded Filter object.
    :type db_filter: Filter
    :param export_path: Path to a dir for new dir creation.
    :type folder_path: Path
    :param groups: A list of supported MySQL column names.
    :type groups: list[str]
    :param conditionals_map: A mapping between group conditionals and Paths.
    :type conditionals_map: dict{Path:list}\
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    :param previous: Value set by function to provide info for print statements.
    :type previous: str
    :param depth: Value set by function to provide info for print statements.
    :type depth: int
    :returns conditionals_map: A mapping between group conditionals and Paths.
    :rtype: dict{Path:list}
    """
    groups = groups.copy()
    conditionals = db_filter.build_where_clauses()
    if not groups:
        conditionals_map.update({export_path : conditionals})
        return

    current_group = groups.pop(0)
    if verbose:
        if depth > 0:
            dots = ".." * depth
            print(f"{dots}Grouping by {current_group} in {previous}...")
        else:
            print(f"Grouping by {current_group}...")

    try:
        group_column = db_filter.get_column(current_group)
    except:
        print(f"Group '{current_group}' is not a valid group.")
        sys.exit(1)

    transposed_values = db_filter.build_values(column=current_group,
                                               where=conditionals)

    if not transposed_values:
        export_path.rmdir()

    for group in transposed_values:
        group_path = export_path.joinpath(str(group))
        group_path.mkdir()
        db_filter_copy = db_filter.copy()
        db_filter_copy.add(f"{current_group}={group}")

        previous = f"{current_group} {group}"
        build_groups_map(db_filter_copy, group_path, conditionals_map,
                                                     groups=groups,
                                                     verbose=verbose,
                                                     previous=previous,
                                                     depth=depth+1)

def get_sort_columns(alchemist, sort_inputs):
    """Function that converts input for sorting to SQLAlchemy Columns.

    :param alchemist: A connected and fully build AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param sort_inputs: A list of supported MySQL column names.
    :type sort_inputs: list[str]
    :returns: A list of SQLAlchemy Column objects.
    :rtype: list[Column]
    """
    sort_columns = []
    for sort_input in sort_inputs:
        try:
            sort_column = querying.get_column(alchemist.metadata, sort_input)
        except ValueError:
            print("Error occured while selecting sort columns.")
            print(f"Column inputted, '{sort_input}', is invalid.")
            sys.exit(1)
        finally:
            sort_columns.append(sort_column)

    return sort_columns

def filter_csv_columns(alchemist, table, include_columns=[], exclude_columns=[],
                                                    sequence_columns=False):
    """Function that filters and constructs a list of Columns to select.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param table: MySQL table name.
    :type table: str
    :param include_columns: A list of supported MySQL column names.
    :type include_columns: list[str]
    :param exclude_columns: A list of supported MySQL column names.
    :type exclude_columns: list[str]
    :param sequence_columns: A boolean to toggle inclusion of sequence data.
    :type sequence_columns: bool
    :returns: A list of SQLAlchemy Column objects.
    :rtype: list[Column]
    """
    table_obj = alchemist.metadata.tables[table]
    starting_columns = list(table_obj.columns)
    primary_key = list(table_obj.primary_key.columns)[0]

    include_column_objs = starting_columns
    for column in include_columns:
        try:
            column_obj = querying.get_column(alchemist.metadata, column)
        except ValueError:
            print("Error occured while selecting csv columns.")
            print(f"Column inputted, '{column}', is invalid.")
            sys.exit(1)
        finally:
            if column_obj not in include_column_objs:
                include_column_objs.append(column_obj)

    sequence_column_objs = []
    if not sequence_columns:
        for sequence_column in SEQUENCE_COLUMNS[table]:
            sequence_column_obj = dict(table_obj.c)[sequence_column]
            sequence_column_objs.append(sequence_column_obj)

    exclude_column_objs = sequence_column_objs
    for column in exclude_columns:
        try:
            column_obj = querying.get_column(alchemist.metadata, column)
        except ValueError:
            print("Error occured while selecting csv columns.")
            print(f"Column inputted, '{column}', is invalid.")
            sys.exit(1)
        finally:
            exclude_column_objs.append(column_obj)
            if column_obj.compare(primary_key):
                print(f"Primary key to {table} cannot be excluded")
                sys.exit(1)

            if column_obj not in exclude_column_objs:
                exclude_column_objs.append(column_obj)

    columns = []
    for column_obj in include_column_objs:
        if column_obj not in exclude_column_objs:
            columns.append(column_obj)

    return columns

def decode_results(results, columns, verbose=False):
    """Function that decodes encoded results from SQLAlchemy generated data.

    :param results: List of data dictionaries from a SQLAlchemy results proxy.
    :type results: list[dict]
    :param columns: SQLAlchemy Column objects.
    :type columns: list[Column]
    """
    for column in columns:
        if column.type.python_type == bytes:
            if verbose:
                print(f"Decoding retrieved {column} data...")
            for result in results:
                if not result[column.name] is None:
                    result[column.name] = result[column.name].decode("utf-8")

def process_cds_features(phage_genome):
    """Function that sorts and processes the Cds objects of a Genome object.

    :param phage_genome: Genome object containing Cds objects.
    :type phage_genome: Genome
    """

    try:
        def _sorting_key(cds_feature): return cds_feature.start
        phage_genome.cds_features.sort(key=_sorting_key)
    except:
        if phage_genome == None:
            raise TypeError
        print("Genome cds features unable to be sorted")
        pass
    for cds_feature in phage_genome.cds_features:
        cds_feature.set_seqfeature()

#----------------------------------------------------------------------------
#TODO Travis
#Functions to be evaluated for another module:
#-----------------------------------------------------------------------------

#Copy of mysqldb.parse_feature_data() with value subquerying.
#Value subquerying needed for +300000 GeneID entries.
#Unsure about function redundancy.
def parse_feature_data(alchemist, values=[], limit=8000):
    """Returns Cds objects containing data parsed from a MySQL database.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param values: List of GeneIDs upon which the query can be conditioned.
    :type values: list[str]
    """
    gene_table = querying.get_table(alchemist.metadata, "gene")
    primary_key = list(gene_table.primary_key.columns)[0]
    cds_data_columns = list(gene_table.c)

    cds_data_query = querying.build_select(alchemist.graph, cds_data_columns)

    cds_data = querying.execute(alchemist.engine, cds_data_query,
                                                  in_column=primary_key,
                                                  values=values,
                                                  limit=limit)

    cds_list = []
    for data_dict in cds_data:
        cds_ftr = mysqldb.parse_gene_table_data(data_dict)
        cds_list.append(cds_ftr)

    return cds_list

#Similar to genome_to_seqrecord()
#Move to flat_files.py?
def cds_to_seqrecord(cds, parent_genome):
    """Creates a SeqRecord object from a Cds and its parent Genome.

    :param cds: A populated Cds object.
    :type cds: Cds
    :param phage_genome: Populated parent Genome object of the Cds object.
    :returns: Filled Biopython SeqRecord object.
    :rtype: SeqRecord
    """
    record = SeqRecord(cds.translation)
    record.seq.alphabet = IUPAC.IUPACAmbiguousDNA()
    record.name = cds.id
    if cds.locus_tag != "":
        record.id = cds.locus_tag

    cds.set_seqfeature()
    record.features = [cds.seqfeature]

    record.description = (f"{cds.description} "
                          f"[{parent_genome.host_genus} phage {cds.genome_id}]")
    record.annotations = get_cds_seqrecord_annotations(cds, parent_genome)

    return record

#Similar to get_seqrecord_annotations():
#Move to flat_files.py?
def get_cds_seqrecord_annotations(cds, parent_genome):
    """Function that creates a Cds SeqRecord annotations attribute dict.
    :param cds: A populated Cds object.
    :type cds: Cds
    :param phage_genome: Populated parent Genome object of the Cds object.
    :type phage_genome: Genome
    :returns: Formatted SeqRecord annotations dictionary.
    :rtype: dict{str}
    """
    annotations = {"molecule type": "DNA",
                   "topology" : "linear",
                   "data_file_division" : "PHG",
                   "date" : "",
                   "accessions" : [],
                   "sequence_version" : "",
                   "keyword" : [],
                   "source" : "",
                   "organism" : "",
                   "taxonomy" : [],
                   "comment" : ()}

    annotations["date"] = parent_genome.date
    annotations["organism"] = (f"{parent_genome.host_genus} phage "
                               f"{cds.genome_id}")
    annotations["source"] = f"Accession {parent_genome.accession}"

    annotations["taxonomy"].append("Viruses")
    annotations["taxonomy"].append("dsDNA Viruses")
    annotations["taxonomy"].append("Caudovirales")

    annotations["comment"] = get_cds_seqrecord_annotations_comments(cds)

    return annotations

#Similar to get_seqrecord_annotatoions():
#Move to flat_files.py?
def get_cds_seqrecord_annotations_comments(cds):
    """Function that creates a Cds SeqRecord comments attribute tuple.

    :param cds:
    :type cds:
    """
    pham_comment =\
           f"Pham: {cds.pham_id}"
    auto_generated_comment =\
            "Auto-generated genome record from a MySQL database"

    return (pham_comment, auto_generated_comment)

def append_database_version(genome_seqrecord, version_data):
    """Function that appends the database version to the SeqRecord comments.

    :param genome_seqrecord: Filled SeqRecord object.
    :type genome_seqfeature: SeqRecord
    :param version_data: Dictionary containing database version information.
    :type version_data: dict
    """
    version_keys = version_data.keys()
    version = "NULL"
    schema_version = "NULL"
    if "Version" in version_keys or "SchemaVersion" not in version_keys:
        version = version_data["Version"]
    if "SchemaVersion" in version_keys:
        schema_version = version_data["SchemaVersion"]


    try:
        genome_seqrecord.annotations["comment"] =\
                genome_seqrecord.annotations["comment"] + (
                    "Database Version: {}; Schema Version: {}".format(
                                                            version,
                                                            schema_version),)
    except:
        if isinstance(genome_seqrecord, SeqRecord):
            return

        raise TypeError("Object must be of type SeqRecord."
                       f"Object was of type {type}.")

#Similar to cds.get_qualifiers()
#Intoduces a way to provide GenPept-formatted seqrecord qualifiers
def get_genpept_cds_qualifiers(cds):
    """Function that uses cds data to populate a genpept-cds qualifiers dict.

    :returns: GenPept-CDS formatted SeqFeature qualifiers dictionary.
    """
    qualifiers = OrderedDict()
    qualifiers["gene"] = [self.name]
    if cds.locus_tag != "":
        qualifiers["locus_tag"] = [self.locus_tag]
    qualifiers["transl_table"] = ["11"]
    if cds.raw_description != "":
        qualifiers[""]

    return qualifiers

def get_protein_cds_qualfiiers(cds):
    """Function that uses cds data to populate a protein qualifiers dict.

    :returns: Protein SeqFeature qualifiers dictionary.
    """
    qualifiers = OrderedDict()
    if cds.raw_description != "":
        qualifiers["product"] = cds.raw_description

    return qualifiers
