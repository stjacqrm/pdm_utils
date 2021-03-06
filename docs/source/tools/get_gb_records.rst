.. _getgbrecords:

get_gb_records: retrieve records from GenBank
=============================================


Genome data in the MySQL database may be directly associated with genome data stored in GenBank. The 'Accession' field in the 'phage' table provides a link to these records, and all GenBank records associated with any particular database can be retrieved using the ``pdm_utils get_gb_records`` tool.

To retrieve all GenBank records relative to your database, indicate the name of the database (e.g. 'Actinobacteriophage'). The '-o ./' indicates the directory where the files should be downloaded (if omitted, the default is the working directory from where the pipeline is called)::

    > python3 -m pdm_utils get_gb_records Actinobacteriophage -o ./


.. note::
    The current version of Actinobacteriophage contains thousands of accession numbers, so retrieving GenBank records for the entire database can be slow.


This tool relies upon the NCBI E-utilities (using a Biopython wrapper), and NCBI requests that you provide information about yourself. The ``get_gb_records`` tool accepts a simple text file containing your information (:ref:`ncbicreds`) using the '-c' flag::

    > python3 -m pdm_utils get_gb_records Actinobacteriophage -o ./ -c ncbi_credentials.txt


The ``get_gb_records`` tool will determine which accessions from the MySQL database are valid, will retrieve all live records from GenBank, and store them locally in GenBank-formatted flat file format.
