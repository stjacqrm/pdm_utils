""" Use this script to import data into Phamerator database using the
UNIX command line interface so that the import process provides
interactive feedback about the import process.
"""



# Built-in libraries
import time, sys, os, getpass, csv, re, shutil
import json, urllib
from datetime import datetime
from classes import Genome



# Import third-party modules
try:
    pass
except ModuleNotFoundError as err:
    print(err)
	sys.exit(1)





#TODO replace with new function
#Get the command line parameters
try:
    database = sys.argv[1]
    phageListDir = sys.argv[2]
    updateFile = sys.argv[3]
except:
    print "\n\n\
            This is a python script to import and update phage genomes in the Phamerator database.\n\
            It requires three arguments:\n\
            First argument: name of MySQL database that will be updated (e.g. 'Actino_Draft').\n\
            Second argument: directory path to the folder of genome files that will be uploaded (genbank-formatted).\n\
            Third argument: directory path to the import table file with the following columns (csv-formatted):\n\
                1. Action to implement on the database (add, remove, replace, update)\n\
                2. PhageID to add or update\n\
                3. Host genus of the updated phage\n\
                4. Cluster of the updated phage\n\
                5. Subcluster of the updated phage\n\
                6. Annotation status of the updated phage (draft, final, gbk)\n\
                7. Annotation authorship of the updated phage (hatfull, gbk)\n\
                8. Gene description field of the updated phage (product, note, function)\n\
                9. Accession of the updated phage\n\
                10. Run mode of the updated phage\n\
                11. PhageID that will be removed or replaced\n\n"
	sys.exit(1)











#TODO replace with new functions
#Expand home directory
home_dir = os.path.expanduser('~')


#Verify the genome folder exists

#Add '/' at the end if it's not there
if phageListDir[-1] != "/":
    phageListDir = phageListDir + "/"


#Expand the path if it references the home directory
if phageListDir[0] == "~":
    phageListDir = home_dir + phageListDir[1:]

#Expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
phageListDir = os.path.abspath(phageListDir)



if os.path.isdir(phageListDir) == False:
    print "\n\nInvalid input for genome folder.\n\n"
    sys.exit(1)






#Verify the import table path exists
#Expand the path if it references the home directory
if updateFile[0] == "~":
    updateFile = home_dir + updateFile[1:]

#Expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
updateFile = os.path.abspath(updateFile)
if os.path.exists(updateFile) == False:
    print "\n\nInvalid input for import table file.\n\n"
    sys.exit(1)











#TODO replace with new function
#Create output directories
date = time.strftime("%Y%m%d")

failed_folder = '%s_failed_upload_files' % date
success_folder = '%s_successful_upload_files' % date

try:
    os.mkdir(os.path.join(phageListDir,failed_folder))
except:
    print "\nUnable to create output folder: %s" % os.path.join(phageListDir,failed_folder)
    sys.exit(1)


try:
    os.mkdir(os.path.join(phageListDir,success_folder))
except:
    print "\nUnable to create output folder: %s" % os.path.join(phageListDir,success_folder)
    sys.exit(1)













### Below - refactored script in progress



import prepare_tickets
from functions import phamerator
from functions import flat_files
from functions import tickets

# TODO command now should include an argument that specifies phage_id_field
# from which phage_id should be assigned as flat files are parsed.


# TODO confirm arguments are structured properly.

# TODO confirm directories and files exist.

# TODO confirm import table file exists.

# TODO create output directories.


# TODO parsing from import table:
# 1. parse ticket data from table. = prepare_tickets()
# 2. set case for all fields. = prepare_tickets()
# 3. confirm all tickets have a valid type. = check_ticket_structure()
# 4. populate Genome objects as necessary.
# 5. retrieve data if needed.
# 6. check for PhageID conflicts.
# 7. confirm correct fields are populated based on ticket type.


# Retrieve import ticket data.
# Data is returned as a list of validated ticket objects.
# list_of_ticket_data = read.csv(ticket_filename)
list_of_tickets = tickets.parse_import_tickets(list_of_ticket_data)



# Evaluate the tickets to ensure they are structured properly.


# TODO not sure if I should pass a list of valid types to this function.
index1 = 0
while index1 < len(ticket_list):
    evaluate.check_ticket_structure(ticket_list[index1],
                                    constants.TICKET_TYPE_SET,
                                    constants.EMPTY_SET,
                                    constants.RUN_MODE_SET)
    index1 += 1


# Now that individual tickets have been validated,
# validate the entire group of tickets.
tickets.compare_tickets(ticket_list)


# Tickets will be matched with other genome data.
# Ticket data will be paired with data from PhagesDB, PhameratorDB,
# and/or a flat file.
list_of_matched_objects = []
index2 = 0
while index2 < len(list_of_tickets):

    matched_data_obj = MatchedGenomes()
    matched_data_obj.ticket = list_of_tickets[index2]
    list_of_matched_objects.append(matched_data_obj)
    index2 += 1

# Using each ticket, construct and populate genome objects as needed.
index3 = 0
while index3 < len(list_of_matched_objects):
    tickets.copy_ticket_to_genome(list_of_matched_objects[index3])
    index3 += 1


# Now check to see if there is any missing data for each genome, and
# retrieve it from phagesdb.
index4 = 0
while index4 < len(list_of_matched_objects):

    # If the ticket genome has fields set to 'retrieve', data is
    # retrieved from PhagesDB and populates a new Genome object.
    matched_object = list_of_matched_objects[index4]
    phagesdb.copy_data_from_phagesdb(matched_object, "add")
    index4 += 1




# Each ticket should now contain all requisite data from PhagesDB.
# Validate each ticket by checking each field in the ticket
# that it is populated correctly.



# TODO check for ticket errors = exit script if not structured correctly.
# Iterate through tickets and collect all evals.



if len(list_of_errors) > 0:
    sys.exit(1)






# TODO at some point annotation_qc and retrieve_record attributes
# will need to be set. These are dependent on the ticket type.
# If genomes are being replace, these fields may be carried over from
# the previous genome, combined with their annotation status.



# Retrieve data from Phamerator.

# TODO create SQL connector object using parsed arguments.
# TODO it may be better to create the SQL object with the
# prepare_phamerator_data module.


# Retrieve all data from Phamerator
# All data is returned as a list of tuples.
retrieved_phamerator_data = phamerator.retrieve_sql_data(sql_obj)


# Now iterate through the phamerator genome dictionary and create
# a second dictionary of parsed Genome objects.

# Create a dictionary of all data retrieved.
# Key = PhageID.
# Value = Genome object with parsed data.
phamerator_data_dict = \
    phamerator.create_phamerator_dict(retrieved_phamerator_data)



# Now that Phamerator data has been retrieved and
# Phamerator genome objects created, match them to ticket data
index5 = 0
while index5 < len(list_of_matched_objects):
    matched_obj = list_of_matched_objects[index5]
    if matched_obj.ticket.type == "replace":
        misc.match_genome_by_phage_id(matched_obj,
                        phamerator_genome_dict,
                        "add")
        phamerator.copy_data_from_phamerator(matched_obj, "add")

    index5 += 1












# TODO when should this be implemented?
# Create sets of unique values for different data fields.
phamerator_data_sets = phamerator.create_data_sets(phamerator_genome_dict)








# TODO check for phamerator data errors = exit script if there are errors
# TODO is this needed?
if len(phamerator_errors) > 0:
    sys.exit(1)






# Parse flat files and create list of genome objects
#TODO insert real function

# Identify valid files in folder.
files_in_folder = basic.identify_files(genome_dir)


# Iterate through the list of files.
# Parse each file into a Genome object.
# Returns lists of Genome objects, Eval objects, parsed files,
# and failed files.
flat_file_genomes, valid_files, failed_files = \
    flat_files.create_parsed_flat_file_list(files_in_folder)

# TODO check for flat file parsing errors = exit script if there are errors.
if len(all_results) > 0:
    sys.exit(1)







# Match tickets to flat file data





# TODO check to confirm that genome objects from parsed flat files do not
# contain any duplicate phage_ids, since that is not gauranteed.


# Create dictionary of flat file data.
flat_file_dict = {}
index100 = 0
while index100 < len(flat_file_genomes):
    genome = flat_file_genomes[index100]
    flat_file_dict[genome.phage_id] = genome



# Match flat file genomes.
index6 = 0
while index6 < len(list_of_matched_objects):
    matched_obj = list_of_matched_objects[index6]
    misc.match_genome_by_phage_id(matched_obj, flat_file_dict, "add")






# TODO don't think this is needed anymore, since 'update' and 'remove'
# tickets aren't valid types for this script.
# TODO Now that all data has been matched, split matched objects by ticket type.
# Different types of tickets are evaluated differently.
# matched_object_dict = create_matched_object_dict(list_of_matched_objects)
#
# list_of_update_objects = matched_object_dict["update"]
# list_of_remove_objects = matched_object_dict["remove"]
# list_of_add_replace_objects = matched_object_dict["add_replace"]





# TODO After parsing flat file, prepare gene_id and gene_name appropriately



# Now that the flat file to be imported is parsed and matched to a ticket,
# use the ticket to populate specific genome-level fields such as
# host, cluster, subcluster, etc.
index7 = 0
while index7 < len(list_of_add_replace_objects):
    matched_object = list_of_add_replace_objects[index7]
    flat_files.copy_data_to_flat_file(matched_object, "add")
    index7 += 1







# Perform all evaluations based on the ticket type.






# TODO after each add_replace ticket is evaluated,
# should the script re-query the database and re-create the
# sets of PhageIDs, Sequences, etc?
index10 = 0
while index10 < len(list_of_matched_objects):
        evaluate.check_datagroup_for_import(list_of_matched_objects[index10])
        list_of_matched_objects[index10].check_for_errors()






# Create all SQL statements for all tickets with no errors.
index11 = 0
while index11 < len(list_of_matched_objects):
        matched_object = list_of_matched_objects[index11]
        if matched_object.errors == 0:
            matched_object.create_sql_statements()




# TODO import all scrubbed add_replace data into Phamerator.














### Unused code below.


#Not sure what to do with this:
failed_actions = []
file_tally = 0
script_warnings = 0
script_errors = 0































###
