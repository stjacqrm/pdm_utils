"""Functions to interact with PhameratorDB."""


from pdm_utils.classes import genome
from pdm_utils.classes import genomepair
from pdm_utils.classes import cds
from pdm_utils.functions import basic


def parse_phage_table_data(data_dict, trans_table=11):
    """Parse a Phamerator database dictionary to create a Genome object.

    :param data_dict:
        Dictionary of data retrieved from the phage table of PhameratorDB.
    :type data_dict: dict
    :param trans_table:
        The translation table that can be used to translate CDS features.
    :type trans_table: int
    :returns: A pdm_utils genome object.
    :rtype: genome
    """

    gnm = genome.Genome()
    try:
        gnm.id = data_dict["PhageID"]
    except:
        pass

    try:
        gnm.accession = data_dict["Accession"]
    except:
        pass

    try:
        gnm.name = data_dict["Name"]
    except:
        pass

    try:
        gnm.host_genus = data_dict["HostStrain"]
    except:
        pass

    try:
        # Sequence data is stored as MEDIUMBLOB, so decode to string.
        gnm.set_sequence(data_dict["Sequence"].decode("utf-8"))
    except:
        pass

    try:
        gnm._length = data_dict["SequenceLength"]
    except:
        pass

    try:
        gnm.date = data_dict["DateLastModified"]
    except:
        pass

    try:
        gnm.description = data_dict["Notes"].decode("utf-8")
    except:
        pass

    try:
        gnm._gc = data_dict["GC"]
    except:
        pass

    try:
        gnm.set_cluster_subcluster(data_dict["Cluster"])
    except:
        pass

    try:
        # Singletons are stored in PhameratorDB as NULL, which gets
        # returned as None.
        gnm.set_cluster(data_dict["Cluster2"])
    except:
        pass

    try:
        gnm.set_subcluster(data_dict["Subcluster2"])
    except:
        pass

    try:
        gnm.annotation_status = data_dict["status"]
    except:
        pass

    try:
        gnm.retrieve_record = data_dict["RetrieveRecord"]
    except:
        pass

    try:
        gnm.annotation_qc = data_dict["AnnotationQC"]
    except:
        pass

    try:
        gnm.annotation_author = data_dict["AnnotationAuthor"]
    except:
        pass

    gnm.translation_table = trans_table
    gnm.type = "phamerator"
    return gnm


def parse_gene_table_data(data_dict, trans_table=11):
    """Parse a Phamerator database dictionary to create a Cds object.

    :param data_dict:
        Dictionary of data retrieved from the gene table of PhameratorDB.
    :type data_dict: dict
    :param trans_table:
        The translation table that can be used to translate CDS features.
    :type trans_table: int
    :returns: A pdm_utils cds object.
    :rtype: cds
    """

    cds_ftr = cds.Cds()
    try:
        cds_ftr.id = data_dict["GeneID"]
    except:
        pass

    try:
        cds_ftr.genome_id = data_dict["PhageID"]
    except:
        pass

    try:
        cds_ftr.left = data_dict["Start"]
    except:
        pass

    try:
        cds_ftr.right = data_dict["Stop"]
    except:
        pass

    try:
        cds_ftr._length = data_dict["Length"]
    except:
        pass

    try:
        cds_ftr.name = data_dict["Name"]
    except:
        pass

    try:
        cds_ftr.type = data_dict["TypeID"]
    except:
        pass

    try:
        cds_ftr.set_translation(data_dict["translation"])
    except:
        pass

    try:
        cds_ftr.strand = data_dict["Orientation"]
    except:
        pass

    try:
        cds_ftr.description = data_dict["Notes"].decode("utf-8")
    except:
        pass

    try:
        cds_ftr.locus_tag = data_dict["LocusTag"]
    except:
        pass

    try:
        cds_ftr.translation_table = trans_table
    except:
        pass
    return cds_ftr


def retrieve_data(sql_handle, column=None, query=None, phage_id_list=None):
    """Retrieve genome data from Phamerator for a single genome.

    The query is modified to include one or more PhageIDs

    :param sql_handle:
        A pdm_utils MySQLConnectionHandler object containing
        information on which database to connect to.
    :type sql_handle: MySQLConnectionHandler
    :param query:
        A MySQL query that selects valid, specific columns
        from the a valid table without conditioning on a PhageID
        (e.g. 'SELECT PhageID, Cluster FROM phage').
    :type query: str
    :param column:
        A valid column in the table upon which the query can be conditioned.
    :type column: str
    :param phage_id_list:
        A list of valid PhageIDs upon which the query can be conditioned.
        In conjunction with the 'column' parameter, the 'query' is
        modified (e.g. "WHERE PhageID IN ('L5', 'Trixie')").
    :type phage_id_list: list
    :returns:
        A list of items, where each item is a dictionary of
        SQL data for each PhageID.
    :rtype: list
    """
    if (phage_id_list is not None and len(phage_id_list) > 0):
        query = query \
                + " WHERE %s IN ('" % column \
                + "','".join(phage_id_list) \
                + "')"
    query = query + ";"
    result_list = sql_handle.execute_query(query)
    sql_handle.close_connection()
    return result_list


def parse_cds_data(sql_handle, column=None, phage_id_list=None, query=None):
    """Returns Cds objects containing data parsed from a
    Phamerator database.

    :param sql_handle:
        This parameter is passed directly to the 'retrieve_data' function.
    :type sql_handle: MySQLConnectionHandler
    :param query:
        This parameter is passed directly to the 'retrieve_data' function.
    :type query: str
    :param column:
        This parameter is passed directly to the 'retrieve_data' function.
    :type column: str
    :param phage_id_list:
        This parameter is passed directly to the 'retrieve_data' function.
    :type phage_id_list: list
    :returns: A list of pdm_utils Cds objects.
    :rtype: list
    """
    cds_list = []
    result_list = retrieve_data(
                    sql_handle, column=column, query=query,
                    phage_id_list=phage_id_list)
    for data_dict in result_list:
        cds_ftr = parse_gene_table_data(data_dict)
        cds_list.append(cds_ftr)
    return cds_list


def parse_genome_data(sql_handle, phage_id_list=None, phage_query=None,
                      gene_query=None, trna_query=None):
    """Returns a list of Genome objects containing data parsed from MySQL
    Phamerator database.

    :param sql_handle:
        This parameter is passed directly to the 'retrieve_data' function.
    :type sql_handle: MySQLConnectionHandler
    :param phage_query:
        This parameter is passed directly to the 'retrieve_data' function
        to retrieve data from the phage table.
    :type phage_query: str
    :param gene_query:
        This parameter is passed directly to the 'parse_cds_data' function
        to retrieve data from the gene table.
        If not None, pdm_utils Cds objects for all of the phage's
        CDS features in the gene table will be constructed
        and added to the Genome object.
    :type gene_query: str
    :param trna_query:
        This parameter is passed directly to the '' function
        to retrieve data from the tRNA table. Note: not yet implemented.
        If not None, pdm_utils Trna objects for all of the phage's
        CDS features in the gene table will be constructed
        and added to the Genome object.
    :type trna_query: str
    :param phage_id_list:
        This parameter is passed directly to the 'retrieve_data' function.
        If there is at at least one valid PhageID, a pdm_utils genome
        object will be constructed only for that phage. If None, or an
        empty list,  genome objects for all phages in the
        database will be constructed.
    :type phage_id_list: list
    :returns: A list of pdm_utils Genome objects.
    :rtype: list
    """
    genome_list = []
    result_list1 = retrieve_data(sql_handle, column="PhageID",
                                             phage_id_list=phage_id_list,
                                             query=phage_query)
    for data_dict in result_list1:
        gnm = parse_phage_table_data(data_dict)
        if gene_query is not None:
            cds_list = parse_cds_data(sql_handle, column="PhageID",
                                      phage_id_list=[gnm.id],
                                      query=gene_query)
            gnm.cds_features = cds_list
        if trna_query is not None:
            # TODO develop this step once tRNA table and objects are built.
            pass
        genome_list.append(gnm)
    return genome_list


# TODO this can be improved if the MCH.execute_query() method
# is able to switch to a standard cursor instead of only using
# dictcursor.
def create_phage_id_set(sql_handle):
    """Create set of phage_ids currently in PhameratorDB.

    :param sql_handle:
        A pdm_utils MySQLConnectionHandler object containing
        information on which database to connect to.
    :type sql_handle: MySQLConnectionHandler
    :returns: A set of PhageIDs.
    :rtype: set
    """
    query = "SELECT PhageID FROM phage"
    # Returns a list of items, where each item is a dictionary of
    # SQL data for each row in the table.
    result_list = sql_handle.execute_query(query)
    sql_handle.close_connection()
    # Convert to a set of PhageIDs.
    result_set = set([])
    for dict in result_list:
        result_set.add(dict["PhageID"])
    return result_set


def create_seq_set(sql_handle):
    """Create set of genome sequences currently in PhameratorDB.

    :param sql_handle:
        A pdm_utils MySQLConnectionHandler object containing
        information on which database to connect to.
    :type sql_handle: MySQLConnectionHandler
    :returns: A set of genome sequences.
    :rtype: set
    """
    query = "SELECT Sequence FROM phage"
    # Returns a list of items, where each item is a dictionary of
    # SQL data for each row in the table.
    result_list = sql_handle.execute_query(query)
    sql_handle.close_connection()
    # Convert to a set of sequences.
    # Sequence data is stored as MEDIUMBLOB, so data is returned as bytes
    # "b'AATT", "b'TTCC", etc.
    result_set = set([])
    for dict in result_list:
        result_set.add(dict["Sequence"].decode("utf-8"))
    return result_set




# TODO unittest.
def create_accession_set(sql_handle):
    """Create set of accessions currently in PhameratorDB.

    :param sql_handle:
        A pdm_utils MySQLConnectionHandler object containing
        information on which database to connect to.
    :type sql_handle: MySQLConnectionHandler
    :returns: A set of accessions.
    :rtype: set
    """
    query = "SELECT Accession FROM phage"
    # Returns a list of items, where each item is a dictionary of
    # SQL data for each row in the table.
    result_list = sql_handle.execute_query(query)
    sql_handle.close_connection()
    # Convert to a set of accessions.
    result_set = set([])
    for dict in result_list:
        result_set.add(dict["Accession"])
    return result_set




def create_update_statement(table, field1, value1, field2, value2):
    """Create MySQL UPDATE statement.

    When the new value to be added is 'singleton' (e.g. for Cluster and
    Cluster2 fields), or an empty value (e.g. None, "none", etc.),
    the new value is set to NULL.

    :param table: The database table to insert information.
    :type table: str
    :param field1: The column upon which the statement is conditioned.
    :type field1: str
    :param value1:
        The value of 'field1' upon which the statement is conditioned.
    :type value1: str
    :param field2: The column that will be updated.
    :type field2: str
    :param value2:
        The value that will be inserted into 'field2'.
    :type value2: str
    :returns: A MySQL query.
    :rtype: set
    """
    part1 = "UPDATE %s SET %s = " % (table, field2)
    part3 = " WHERE %s = '%s';" % (field1, value1)
    part2a = "NULL"
    part2b = "'%s'" % value2
    if (basic.check_empty(value2) == True or \
        value2.lower() == "singleton"):
        part2 = part2a
    else:
        part2 = part2b
    statement = part1 + part2 + part3
    return statement



def create_genome_update_statements(gnm):
    """Create a collection of genome-level UPDATE statements using data
    in a Genome object.
    """

    table = "phage"
    field1 = "PhageID"
    value1 = gnm.id
    statements = []
    statements.append(create_update_statement( \
        table, field1, value1, "HostStrain", gnm.host_genus))
    statements.append(create_update_statement( \
        table, field1, value1, "status", gnm.annotation_status))
    statements.append(create_update_statement( \
        table, field1, value1, "Accession", gnm.accession))
    statements.append(create_update_statement( \
        table, field1, value1, "AnnotationAuthor", gnm.author))
    statements.append(create_update_statement( \
        table, field1, value1, "Cluster", gnm.cluster_subcluster))
    statements.append(create_update_statement( \
        table, field1, value1, "Cluster2", gnm.cluster))
    statements.append(create_update_statement( \
        table, field1, value1, "Subcluster2", gnm.subcluster))
    return statements


def create_delete_statement(table, field1, data1):
    """Create MySQL DELETE statement."""
    statement = "DELETE FROM %s WHERE %s = '%s';" % (table, field1, data1)
    return statement


# TODO this may no longer be needed.
def create_genome_delete_statement(gnm):
    """Create a genome-level DELETE statements using data
    in a Genome object."""

    table = "phage"
    field1 = "PhageID"
    value1 = gnm.id
    statements = []
    statements.append(create_delete_statement(table, field1, value1))
    return statements


def create_cds_insert_statement(cds_feature):
    """Create a CDS-level INSERT statement using data in a CDS object."""

    statement = "INSERT INTO gene " + \
        "(GeneID, PhageID, Start, Stop, Length, Name, TypeID, " + \
        "translation, Orientation, Notes, LocusTag) " + \
        "VALUES " + \
        "('%s', '%s', %s, %s, %s, '%s', '%s', '%s', '%s', '%s', '%s');" % \
        (cds_feature.id, \
        cds_feature.genome_id, \
        cds_feature.left, \
        cds_feature.right, \
        cds_feature._translation_length, \
        cds_feature.name, \
        cds_feature.type, \
        cds_feature.translation, \
        cds_feature.strand, \
        cds_feature.processed_description, \
        cds_feature.locus_tag)
    return statement


# TODO this function could also receive a genome object.
def create_cds_insert_statements(list_of_features):
    """Create a collection of CDS-level INSERT statements using data
    in a list of CDS objects."""

    statements = []
    for cds_feature in list_of_features:
        statements.append(create_cds_insert_statement(cds_feature))
    return statements


def create_genome_insert_statement(gnm):
    """Create a genome-level INSERT statements using data
    in a Genome object."""

    statement = \
        "INSERT INTO phage (PhageID, Accession, Name, " + \
        "HostStrain, Sequence, SequenceLength, GC, status, " + \
        "DateLastModified, RetrieveRecord, AnnotationQC, " + \
        "AnnotationAuthor) " + \
        "VALUES (" + \
        "'%s', '%s', '%s', '%s', '%s', %s, %s, '%s', '%s', '%s', '%s', '%s');" \
        % (gnm.id, \
        gnm.accession, \
        gnm.name, \
        gnm.host_genus, \
        gnm.seq, \
        gnm._length, \
        gnm._gc, \
        gnm.annotation_status, \
        gnm.date, \
        gnm.retrieve_record, \
        gnm.annotation_qc, \
        gnm.annotation_author)
    return statement


def create_genome_insert_statements(gnm):
    """Create a collection of genome-level INSERT statements using data
    in a Genome object."""

    table = "phage"
    field1 = "PhageID"
    value1 = gnm.id
    statements = []
    statements.append(create_genome_insert_statement(gnm))
    statements.append(create_update_statement( \
        table, field1, value1, "Cluster", gnm.cluster_subcluster))
    statements.append(create_update_statement( \
        table, field1, value1, "Cluster2", gnm.cluster))
    statements.append(create_update_statement( \
        table, field1, value1, "Subcluster2", gnm.subcluster))
    return statements


def copy_data_from(bndl, type, flag="retain"):
    """Copy data from a 'phamerator' genome object.

    If a genome object stored in the Bundle object has
    attributes that are set to be 'retained' from Phamerator,
    copy any necessary data from the genome with 'type' attribute
    set to 'phamerator' to the new genome.

    :param bndl: A pdm_utils Bundle object.
    :type bndl: Bundle
    :param type:
        Indicates the value of the target genome's 'type',
        indicating the genome to which data will be copied.
    :type type: str
    :param flag:
        Indicates the value that attributes of the target genome object
        must have in order be updated from the 'phamerator' genome object.
    :type flag: str
    """
    if type in bndl.genome_dict.keys():
        genome1 = bndl.genome_dict[type]
        genome1.set_value_flag(flag)
        if genome1._value_flag:
            if "phamerator" in bndl.genome_dict.keys():
                genome2 = bndl.genome_dict["phamerator"]

                # Copy all data that is set to be copied and
                # add to Bundle object.
                genome_pair = genomepair.GenomePair()
                genome_pair.genome1 = genome1
                genome_pair.genome2 = genome2
                genome_pair.copy_data("type", genome2.type, genome1.type, flag)
                bndl.set_genome_pair(genome_pair, genome1.type, genome2.type)

        # Now record an error if there are still fields
        # that need to be retained.
        genome1.set_value_flag(flag)
        genome1.check_value_flag()




























# TODO unit test below.

















# TODO need to work on this.
# TODO implement.
# TODO unit test.
def implement_update_statements():

    #If it looks like there is a problem with some of the genomes on the list,
    #cancel the transaction, otherwise proceed
    if updated == update_total:
        if run_type == "production":
            con = mdb.connect(mysqlhost, username, password, database)
            con.autocommit(False)
            cur = con.cursor()

            try:
                cur.execute("START TRANSACTION")
                for statement in update_statements:
                    cur.execute(statement)
                    write_out(output_file,"\n" + statement + " executed successfully, but not yet committed.")
                cur.execute("COMMIT")
                write_out(output_file,"\nAll update statements committed.")
                cur.close()
                con.autocommit(True)

            except:
                success_action_file_handle.close()
                mdb_exit("\nError: problem updating genome information.\nNo changes have been made to the database.")

            con.close()
        else:
            write_out(output_file,"\nRUN TYPE IS %s, SO NO CHANGES TO THE DATABASE HAVE BEEN IMPLEMENTED.\n" % run_type)
    else:
        write_out(output_file,"\nError: problem processing data list to update genomes. Check input table format.\nNo changes have been made to the database.")
        write_out(output_file,"\nExiting import script.")
        output_file.close()
        success_action_file_handle.close()
        sys.exit(1)

    #Document the update actions
    for element in update_data_list:
        if element[7] == "":
            element[7] = "none"

        update_output_list = [element[0],\
                                element[1],\
                                element[2],\
                                element[3],\
                                element[8],\
                                element[4],\
                                author_dictionary[element[9]],\
                                element[5],\
                                element[7],\
                                element[10],\
                                element[6]]
        success_action_file_writer.writerow(update_output_list)

    write_out(output_file,"\nAll field update actions have been implemented.")
    raw_input("\nPress ENTER to proceed to next import stage.")




# TODO need to work on this.
# TODO implement.
# TODO unit test.
def implement_remove_statements():

    #If it looks like there is a problem with some of the genomes on the list,
    #cancel the transaction, otherwise proceed

    if removed == remove_total:

        if run_type == "production":
            con = mdb.connect(mysqlhost, username, password, database)
            con.autocommit(False)
            cur = con.cursor()

            try:
                cur.execute("START TRANSACTION")
                for statement in removal_statements:
                    cur.execute(statement)
                    write_out(output_file,"\n" + statement + " executed successfully, but not yet committed.")
                cur.execute("COMMIT")
                write_out(output_file,"\nAll remove statements committed.")
                cur.close()
                con.autocommit(True)

            except:
                success_action_file_handle.close()
                mdb_exit("\nError: problem removing genomes with no replacements.\nNo remove actions have been implemented.")
            con.close()
        else:
            write_out(output_file,"\nRUN TYPE IS %s, SO NO CHANGES TO THE DATABASE HAVE BEEN IMPLEMENTED.\n" % run_type)
    else:
        write_out(output_file,"\nError: problem processing data list to remove genomes. Check input table format.\nNo remove actions have been implemented.")
        output_file.close()
        success_action_file_handle.close()
        sys.exit(1)

    #Document the remove actions
    for element in remove_data_list:
        remove_output_list = [element[0],\
                                element[1],\
                                element[2],\
                                element[3],\
                                element[8],\
                                element[4],\
                                element[9],\
                                element[5],\
                                element[7],\
                                element[10],\
                                element[6]]
        success_action_file_writer.writerow(remove_output_list)
    write_out(output_file,"\nAll genome remove actions have been implemented.")
    raw_input("\nPress ENTER to proceed to next import stage.")















#TODO below: functions that may no longer be needed.







# # TODO this may no longer be needed now that
# # parse_phage_table_data() is available.
# def parse_phamerator_data(gnm, data_tuple):
#     """Parses tuple of data derived from a Phamerator database
#     and populates a genome object.
#     Expected data structure:
#     0 = PhageID
#     1 = Name
#     2 = HostStrain
#     3 = Sequence
#     4 = status
#     5 = Cluster2
#     6 = DateLastModified
#     7 = Accession
#     8 = Subcluster2
#     9 = AnnotationAuthor
#     10 = AnnotationQC
#     11 = RetrieveRecord
#     """
#
#     gnm.set_id(data_tuple[0])
#     gnm.name = data_tuple[1]
#     gnm.set_host_genus(data_tuple[2])
#     gnm.set_sequence(data_tuple[3])
#     gnm.annotation_status = data_tuple[4]
#     gnm.set_cluster(data_tuple[5])
#     gnm.set_subcluster(data_tuple[8])
#     gnm.set_date(data_tuple[6])
#     gnm.set_accession(data_tuple[7])
#     gnm.annotation_author = str(data_tuple[9])
#     gnm.annotation_qc = str(data_tuple[10])
#     gnm.retrieve_record = str(data_tuple[11])
#     gnm.type = "phamerator"





# TODO this may no longer be needed now that
# parse_phage_table_data() is available.
# def create_phamerator_dict(phamerator_data_tuples):
#     """
#     Returns a dictionary of Phamerator data retrieved from MySQL query.
#     Key = PhageID.
#     Value = Genome object containing parsed MySQL data.
#     """
#
#     genome_dict = {}
#     for genome_tuple in phamerator_data_tuples:
#         gnm = genome.Genome()
#         parse_phamerator_data(gnm,genome_tuple)
#         genome_dict[gnm.id] = gnm
#
#     return genome_dict

#
# # TODO this may no longer be needed.
# def create_data_sets(genome_dict):
#     """
#     Create sets of all unique values for several fields in the Phamerator data.
#     """
#     phage_id_set = set()
#     host_genus_set = set()
#     status_set = set()
#     cluster_set = set()
#     accession_set = set()
#     subcluster_set = set()
#
#     for genome_id in genome_dict.keys():
#
#         gnm = genome_dict[genome_id]
#         phage_id_set.add(gnm.id)
#         host_genus_set.add(gnm.host_genus)
#         status_set.add(gnm.annotation_status)
#         cluster_set.add(gnm.cluster)
#
#         # TODO this was not implemented in original import script,
#         # so maybe the subcluster 'empty check' is not needed.
#         # Only add to the accession set if there was an accession,
#         # and not if it was empty.
#         if basic.check_empty(gnm.subcluster) == False:
#             subcluster_set.add(gnm.subcluster)
#
#         # Only add to the accession set if there was an accession,
#         # and not if it was empty.
#         if basic.check_empty(gnm.accession) == False:
#             accession_set.add(gnm.accession)
#
#     dictionary_of_sets = {}
#     dictionary_of_sets["phage_id"] = phage_id_set
#     dictionary_of_sets["host_genus"] = host_genus_set
#     dictionary_of_sets["annotation_status"] = status_set
#     dictionary_of_sets["cluster"] = cluster_set
#     dictionary_of_sets["subcluster"] = subcluster_set
#     dictionary_of_sets["accession"] = accession_set
#
#     return dictionary_of_sets

###