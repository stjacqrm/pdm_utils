import re
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from networkx import Graph
from networkx import shortest_path
from sqlalchemy import Column
from sqlalchemy import and_
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.exc import InternalError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.sql import functions
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.elements import Grouping
from sqlalchemy.sql.elements import UnaryExpression


from pdm_utils.functions import querying
from pdm_utils.functions.mysqldb_basic import query_dict_list

# Import helper functions to build mock database
unittest_file = Path(__file__)
test_dir = unittest_file.parent.parent
if str(test_dir) not in set(sys.path):
    sys.path.append(str(test_dir))
import test_db_utils

class TestQuerying(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        test_db_utils.create_filled_test_db()

    @classmethod
    def tearDownClass(self):
        test_db_utils.remove_db()

    def setUp(self):
        self.engine = create_engine(test_db_utils.create_engine_string())

        session_maker_obj = sessionmaker(bind=self.engine)
        self.session = session_maker_obj()

        self.metadata = MetaData(bind=self.engine)
        self.metadata.reflect()

        self.mapper = automap_base(metadata=self.metadata)
        self.mapper.prepare()

        self.graph = querying.build_graph(self.metadata)

        self.phage = self.metadata.tables["phage"]
        self.gene = self.metadata.tables["gene"]
        self.trna = self.metadata.tables["trna"]

        self.PhageID = self.phage.c.PhageID
        self.Cluster = self.phage.c.Cluster
        self.Subcluster = self.phage.c.Subcluster
        self.GeneID = self.gene.c.GeneID
        self.PhamID = self.gene.c.PhamID
        self.TrnaID = self.trna.c.GeneID
        self.AminoAcid = self.trna.c.AminoAcid

    def test_get_table_1(self):
        """Verify get_table() retrieves correct Table.
        """
        self.assertEqual(querying.get_table(self.metadata, "phage"), self.phage)

    def test_get_table_2(self):
        """Verify get_table() operates case insensitive.
        """
        self.assertEqual(querying.get_table(self.metadata, "pHAgE"), self.phage)

    def test_get_table_3(self):
        """Verify get_table() raises ValueError from invalid table name.
        """
        with self.assertRaises(ValueError):
            querying.get_table(self.metadata, "not_a_table")

    def test_get_column_1(self):
        """Verify get_column() retrieves correct Column.
        """
        self.assertEqual(querying.get_column(self.metadata, "gene.GeneID"),
                                                             self.GeneID)

    def test_get_column_2(self):
        """Verify get_column() retrieves correct Column.
        """
        self.assertEqual(querying.get_column(self.metadata, "GENE.GENEID"),
                                                             self.GeneID)

    def test_get_column_3(self):
        """Verify get_column() raises ValueError from invalid column name.
        """
        with self.assertRaises(ValueError):
            querying.get_column(self.metadata, "gene.not_a_column")

    def test_build_graph_1(self):
        """Verify build_graph() returns a Graph object.
        """
        self.assertTrue(isinstance(self.graph, Graph))

    def test_build_graph_2(self):
        """Verify build_graph() correctly structures Graph nodes.
        """
        self.assertTrue("phage" in self.graph.nodes)
        self.assertTrue("gene" in self.graph.nodes)
        self.assertTrue("trna" in self.graph.nodes)

    def test_build_graph_3(self):
        """Verify build_graph correctly stores Table objects.
        """
        phage_node = self.graph.nodes["phage"]
        gene_node = self.graph.nodes["gene"]
        trna_node = self.graph.nodes["trna"]

        self.assertEqual(phage_node["table"], self.phage)
        self.assertEqual(gene_node["table"], self.gene)
        self.assertEqual(trna_node["table"], self.trna)

    def test_build_graph_4(self):
        """Verify build_graph() correctly stores its MetaData object.
        """
        self.assertEqual(self.graph.graph["metadata"], self.metadata)

    def test_build_where_clause_1(self):
        """Verify build_where_clause() returns a BinaryExpression object.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                        "phage.PhageID=Trixie")

        self.assertTrue(isinstance(where_clause, BinaryExpression))

    def test_build_where_clause_2(self):
        """Verify build_where_clause() builds from specified Column.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                        "phage.PhageID=Trixie")

        self.assertEqual(where_clause.left, self.PhageID)

    def test_build_where_clause_3(self):
        """Verify build_where_clause() builds from specified value.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                        "phage.PhageID=Trixie")

        self.assertEqual(where_clause.right.value, "Trixie")

    def test_extract_columns_1(self):
        """Verify extract_columns() extracts from BooleanClauseLists.
        """
        phageid_clause = (self.PhageID == "Trixie")
        cluster_clause = (self.Cluster == "A")
        phamid_clause  = (self.PhamID == 2)

        clauses = [phageid_clause, cluster_clause, phamid_clause]
        and_clauses = and_(*clauses)
        expected_columns = [self.PhageID, self.Cluster, self.PhamID]

        column_output = querying.extract_columns(and_clauses)

        self.assertEqual(expected_columns, column_output)

    def test_extract_columns_2(self):
        """Verify extract_columns() extracts layered BooleanClauseList.
        """
        phageid_clause = (self.PhageID == "Trixie")
        cluster_clause = (self.Cluster == "A")
        phamid_clause  = (self.PhamID == 2)

        subcluster_clause = (self.Subcluster == "A2")

        clauses = [phageid_clause, cluster_clause, phamid_clause]
        and_clauses = and_(*clauses)
        or_clauses = or_(and_clauses, subcluster_clause)
        expected_columns = [self.PhageID, self.Cluster, self.PhamID,
                            self.Subcluster]

        column_output = querying.extract_columns(or_clauses)

        self.assertEqual(expected_columns, column_output)

    def test_build_onclause_1(self):
        """Verify build_onclause() returns a BinaryExpression object.
        """
        onclause = querying.build_onclause(self.graph, "gene", "phage")

        self.assertTrue(isinstance(onclause, BinaryExpression))

    def test_build_onclause_2(self):
        """Verify build_onclause() builds onclause with conserved direction.
        build_onclause() should build from primary key to foreign key.
        """
        onclause = querying.build_onclause(self.graph, "gene", "phage")

        self.assertEqual(onclause.left.table, self.phage)
        self.assertEqual(onclause.right.table, self.gene)

    def test_build_onclause_3(self):
        """Verify build_onclause() builds onclause with conserved direction.
        build_onclause() should build form primary key to foreign key.
        """
        onclause = querying.build_onclause(self.graph, "phage", "gene")

        self.assertEqual(onclause.left.table, self.phage)
        self.assertEqual(onclause.right.table, self.gene)

    def test_build_onclause_4(self):
        """Verify build_onclause() raises KeyError when Tables are not linked.
        """
        with self.assertRaises(KeyError):
            querying.build_onclause(self.graph, "gene", "trna")

    def test_get_table_list_1(self):
        """Verify get_table_list() returns correct ordered Tables.
        """
        columns = [self.GeneID, self.PhageID, self.TrnaID]

        table_list = querying.get_table_list(columns)

        self.assertEqual(table_list[0], self.gene)
        self.assertEqual(table_list[1], self.phage)
        self.assertEqual(table_list[2], self.trna)

    def test_get_table_list_2(self):
        """Verify get_table_list() accepts Column input.
        """
        table_list = querying.get_table_list(self.AminoAcid)

        self.assertEqual(table_list[0], self.trna)

    def test_get_table_list_3(self):
        """Verify get_table_list() does not return table duplicates.
        """
        table_list = querying.get_table_list([self.PhageID, self.Cluster])

        self.assertTrue(len(table_list) == 1)

    def test_get_table_pathing_1(self):
        """Verify get_table_pathing() builds from common center table.
        """
        table_list = [self.phage, self.gene, self.trna]

        table_pathing = querying.get_table_pathing(self.graph, table_list)

        self.assertEqual(table_pathing[0], self.phage)
        self.assertEqual(table_pathing[1][0], ["phage", "gene"])
        self.assertEqual(table_pathing[1][1], ["phage", "trna"])

    def test_get_table_pathing_2(self):
        """Verify get_table_pathing() builds from distal center table.
        """
        table_list = [self.gene, self.phage, self.trna]

        table_pathing = querying.get_table_pathing(self.graph, table_list)

        self.assertEqual(table_pathing[0], self.gene)
        self.assertEqual(table_pathing[1][0], ["gene", "phage"])
        self.assertEqual(table_pathing[1][1], ["gene", "phage", "trna"])

    def test_get_table_pathing_3(self):
        """Verify get_table_pathing() correctly utilizes center_table input.
        """
        table_list = [self.gene, self.phage, self.trna]

        table_pathing = querying.get_table_pathing(self.graph, table_list,
                                                   center_table=self.phage)

        self.assertEqual(table_pathing[0], self.phage)
        self.assertEqual(table_pathing[1][0], ["phage", "gene"])
        self.assertEqual(table_pathing[1][1], ["phage", "trna"])

    def test_join_pathed_tables_1(self):
        """Verify join_pathed_tables() joins Tables in specified order.
        """
        table_pathing = [self.phage, [["phage", "gene"],
                                      ["phage", "trna"]]]

        joined_tables = querying.join_pathed_tables(self.graph, table_pathing)

        last_table = joined_tables.right
        joined_tables = joined_tables.left
        self.assertEqual(last_table, self.trna)

        second_table = joined_tables.right
        first_table = joined_tables.left
        self.assertEqual(second_table, self.gene)

        self.assertEqual(first_table, self.phage)

    def test_join_pathed_tables_2(self):
        """Verify join_pathed_tables() recognizes already pathed Tables.
        """
        table_pathing = [self.gene, [["gene", "phage"],
                                     ["gene", "phage", "trna"]]]

        joined_tables = querying.join_pathed_tables(self.graph, table_pathing)

        last_table = joined_tables.right
        joined_tables = joined_tables.left
        self.assertEqual(last_table, self.trna)

        second_table = joined_tables.right
        first_table = joined_tables.left
        self.assertEqual(second_table, self.phage)

        self.assertEqual(first_table, self.gene)

    def test_build_select_1(self):
        """Verify build_select() creates valid SQLAlchemy executable.
        """
        select_query = querying.build_select(self.graph, self.PhageID)

        phage_ids = []
        dict_list = query_dict_list(self.engine, select_query)
        for dict in dict_list:
            phage_ids.append(dict["PhageID"])

        self.assertTrue("Myrna" in phage_ids)
        self.assertTrue("D29" in phage_ids)
        self.assertTrue("Trixie" in phage_ids)

    def test_build_select_2(self):
        """Verify build_select() appends WHERE clauses to executable.
        """
        where_clause = (self.Cluster == "A")
        select_query = querying.build_select(self.graph, self.PhageID,
                                                        where=where_clause)

        phage_ids = []
        dict_list = query_dict_list(self.engine, select_query)
        for dict in dict_list:
            phage_ids.append(dict["PhageID"])

        self.assertTrue("Trixie" in phage_ids)
        self.assertTrue("D29" in phage_ids)
        self.assertFalse("Myrna" in phage_ids)

    def test_build_select_3(self):
        """Verify build_select() appends ORDER BY clauses to executable.
        """
        select_query = querying.build_select(self.graph, self.PhageID,
                                                        order_by=self.PhageID)

        dict_list = query_dict_list(self.engine, select_query)

        phage_ids = []
        dict_list = query_dict_list(self.engine, select_query)
        for dict in dict_list:
            phage_ids.append(dict["PhageID"])

        self.assertEqual("Alice", phage_ids[0])
        self.assertTrue("Myrna" in phage_ids)
        self.assertTrue("D29" in phage_ids)
        self.assertTrue("Trixie" in phage_ids)

    def test_build_select_4(self):
        """Verify build_select() handles many-to-one relations as expected.
        build_select() queries should duplicate 'one' when filtering 'many'
        """
        where_clause = (self.Subcluster == "A2")
        select_query = querying.build_select(self.graph, self.Cluster,
                                                        where=where_clause)

        dict_list = query_dict_list(self.engine, select_query)

        self.assertTrue(len(dict_list) > 1)

    def test_build_count_1(self):
        """Verify build_count() creates valid SQLAlchemy executable.
        """
        count_query = querying.build_count(self.graph, self.PhageID)

        dict_list = query_dict_list(self.engine, count_query)
        count_dict = dict_list[0]

        self.assertTrue(isinstance(count_dict["count_1"], int))

    def test_build_count_2(self):
        """Verify build_count() appends WHERE clauses to executable.
        """
        where_clause = (self.PhageID == "Trixie")
        count_query = querying.build_count(self.graph, self.PhageID,
                                                        where=where_clause)

        dict_list = query_dict_list(self.engine, count_query)
        count_dict = dict_list[0]

        self.assertEqual(count_dict["count_1"], 1)

    def test_build_count_3(self):
        """Verify build_count() recognizes multiple inputs as expected.
        """
        where_clause = (self.Cluster == "A")
        count_query = querying.build_count(self.graph,
                                                [self.PhageID,
                                                 self.Cluster.distinct()],
                                                        where=where_clause)

        dict_list = query_dict_list(self.engine, count_query)
        count_dict = dict_list[0]

        self.assertTrue(count_dict["count_1"] > 1)
        self.assertEqual(count_dict["count_2"], 1)

    def test_build_distinct_1(self):
        """Verify build_distinct() handles many-to-one relations as expected.
        build_distinct() should not duplicate 'one' when handling 'many.'
        """
        where_clause = (self.Subcluster == "A2")
        distinct_query = querying.build_distinct(self.graph, self.Cluster,
                                                        where=where_clause)

        dict_list = query_dict_list(self.engine, distinct_query)
        self.assertEqual(len(dict_list), 1)

        distinct_dict = dict_list[0]
        self.assertEqual(distinct_dict["Cluster"], "A")

    def test_build_distinct_2(self):
        """Verify build_distinct() cannot variable aggregated columns.
        MySQL does not accept DISTINCT queries with aggregated
        and non-aggregated columns.
        """
        distinct_query = querying.build_distinct(self.graph,
                                                    [self.PhageID,
                                                     func.count(self.Cluster)])


        with self.assertRaises(InternalError):
            dict_list = query_dict_list(self.engine, distinct_query)

    def test_execute_1(self):
        """Verify execute() correctly executes SQLAlchemy select objects.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                   "phage.Cluster=A")
        phage_table = querying.get_table(self.metadata, "phage")
        select = querying.build_select(self.graph, phage_table,
                                       where=where_clause)

        results = querying.execute(self.engine, select)
        result_keys = results[0].keys()

        self.assertTrue("PhageID" in result_keys)
        self.assertTrue("Cluster" in result_keys)
        self.assertTrue("Subcluster" in result_keys)

    def test_execute_2(self):
        """Verify execute() retrieves expected data.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                   "phage.Cluster=A")
        phage_table = querying.get_table(self.metadata, "phage")
        select = querying.build_select(self.graph, phage_table,
                                       where=where_clause)

        results = querying.execute(self.engine, select)

        for result in results:
            self.assertEqual(result["Cluster"], "A")

    def test_first_column_1(self):
        """Verify first_column() returns expected data type.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                   "phage.Cluster=A")
        phageid = querying.get_column(self.metadata, "phage.PhageID")
        select = querying.build_select(self.graph, phageid,
                                       where=where_clause)

        results = querying.first_column(self.engine, select)

        self.assertTrue(isinstance(results, list))
        self.assertTrue(isinstance(results[0], str))

    def test_first_column_2(self):
        """Verify first_column() retrieves expected data.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                   "phage.Cluster=A")
        phageid = querying.get_column(self.metadata, "phage.PhageID")
        select = querying.build_select(self.graph, phageid,
                                       where=where_clause)

        results = querying.first_column(self.engine, select)

        self.assertTrue("Trixie" in results)
        self.assertTrue("D29" in results)
        self.assertFalse("Myrna" in results)

    def test_execute_value_subqueries(self):
        """Verify execute_value_subqueries() retrieves expected data.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                   "phage.Cluster=A")
        phage_table = querying.get_table(self.metadata, "phage")
        phageid = querying.get_column(self.metadata, "phage.PhageID")
        select = querying.build_select(self.graph, phage_table,
                                       where=where_clause)

        results = querying.execute_value_subqueries(self.engine, select,
                                                    phageid,
                                                    ["Trixie", "D29",
                                                     "Alice", "Myrna"],
                                                    limit=2)

        for result in results:
            self.assertEqual(result["Cluster"], "A")

    def test_first_column_value_subqueries(self):
        """Verify first_column_value_subqueries() retrieves expected data.
        """
        where_clause = querying.build_where_clause(self.graph,
                                                   "phage.Cluster=A")
        phageid = querying.get_column(self.metadata, "phage.PhageID")
        select = querying.build_select(self.graph, phageid,
                                       where=where_clause)

        results = querying.first_column_value_subqueries(self.engine, select,
                                                         phageid,
                                                         ["Trixie", "D29",
                                                          "Alice", "Myrna"],
                                                         limit=2)

        self.assertTrue("Trixie" in results)
        self.assertTrue("D29" in results)
        self.assertFalse("Alice" in results)
        self.assertFalse("Myrna" in results)

    def test_query_1(self):
        """Verify query() correctly queries for SQLAlchemy ORM instances.
        """
        phage_map = self.mapper.classes["phage"]

        instances = querying.query(self.session, self.graph, phage_map)

        first_instance = instances[0]

        first_instance.PhageID
        first_instance.Cluster
        first_instance.Subcluster

        self.session.close()

    def test_query_2(self):
        """Verify query() retrieves expected data.
        """
        phage_map = self.mapper.classes["phage"]

        instances = querying.query(self.session, self.graph, phage_map,
                                            where=phage_map.Cluster=="A")

        phageids = []
        for instance in instances:
            phageids.append(instance.PhageID)

        self.assertTrue("Trixie" in phageids)
        self.assertTrue("D29" in phageids)
        self.assertFalse("Myrna" in phageids)

        self.session.close()

if __name__ == "__main__":
    unittest.main()
