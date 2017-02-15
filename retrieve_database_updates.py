#!/usr/bin/env python
#Database comparison script
#University of Pittsburgh
#Travis Mavrich
#20170212
#The purpose of this script is to provide an interactive environment to retrieve several types of Phamerator updates\
#that will be implemented through import_phage.py script.
#This script has combined the following independent scripts:
#1. compare_databases.py
#2. retrieve_draft_genomes.py
#3. retrieve_phagesdb_flatfiles.py
#4. retrieve_ncbi_phage.py



#Flow of the import process:
#1 Import python modules, set up variables and functions
#2 Option 1: compare Phamerator and phagesdb databases
#3 Option 2: retrieve auto-annotated files from PECAAN
#4 Option 3: retrieve manually-annotated files from phagesdb
#5 Option 4: retrieve updated files from NCBI



#All import tickets created are formatted as follows:
#0 = Import action
#1 = New phageID
#2 = HostStrain
#3 = Cluster
#4 = Status
#5 = Gene description field
#6 = Phage to replace






####Do I need to close json connections?




#Built-in libraries
import time, sys, os, getpass, csv, re, shutil
import json, urllib, urllib2
from datetime import datetime


#Third-party libraries
try:
    import MySQLdb as mdb
    from Bio import SeqIO, Entrez
except:
    print "\nUnable to import one or more of the following third-party modules: MySQLdb."
    print "Install modules and try again.\n\n"
    sys.exit(1)






#Get the command line parameters
try:
    database = sys.argv[1] #What Phamerator database should be compared to phagesdb?
    updateFileDir = sys.argv[2] #What is the directory into which the report should go
    
except:
    print "\n\n\
            This is a python script to retrieve several types of Phamerator database updates.\n\
                1. It compares Phamerator and phagesdb databases to identify inconsistencies.\n\
                2. It retrieves auto-annotated Genbank-formatted flatfiles from PECAAN.\n\
                3. It retrieves manually annotated Genbank-formatted flatfiles from phagesdb.\n\
                4. It retrieves updated Genbank-formatted flatfiles from NCBI.\n\n\n\
            It requires three arguments:\n\
            First argument: name of MySQL database that will be checked (e.g. 'Actino_Draft').\n\
            Second argument: directory path to where all reports, update import tables, and retrieved files will be generated.\n\
            Third argument: list of phages that have manually-annotated files available on phagesdb (csv-formatted):\n\
                    1. phagesdb phage name\n\
                    (Indicate 'none' if this option will not be requested)\n\n\n\
            All retrieval options create a genomes folder and an import table if updates are available (csv-formatted):\n\
                    1. Action to implement on the database (add, remove, replace, update)\n\
                    2. PhageID to add or update\n\
                    3. Host genus of the updated phage\n\
                    4. Cluster of the updated phage\n\
                    5. Field that contains the gene description information (product, note, function)\n\
                    6. PhageID that will be removed or replaced\n\n"
    sys.exit(1)




#Expand home directory
home_dir = os.path.expanduser('~')


#Verify the folder for the consistency report exists

#Add '/' at the end if it's not there
if updateFileDir[-1] != "/":
    updateFileDir = updateFileDir + "/"


#Expand the path if it references the home directory
if updateFileDir[0] == "~":
    updateFileDir = home_dir + updateFileDir[1:]

#Expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
updateFileDir = os.path.abspath(updateFileDir)


if os.path.isdir(updateFileDir) == False:
    print "\n\nInvalid input for output folder.\n\n"
    sys.exit(1)




#Check to see if the user has indicated a phage file.
#If so, verify the path exists for the phage list file
if phage_file.lower() != "none":

    #Expand the path if it references the home directory
    if phage_file[0] == "~":
        phage_file = home_dir + phage_file[1:]

    #Expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
    phage_file = os.path.abspath(phage_file)

    if os.path.exists(phage_file) == False:
        print "\n\nInvalid input for phage list file.\n\n"
        sys.exit(1)







#Set up MySQL parameters
mysqlhost = 'localhost'
print "\n\n"
username = getpass.getpass(prompt='mySQL username:')
print "\n\n"
password = getpass.getpass(prompt='mySQL password:')
print "\n\n"




#Set up other variables
date = time.strftime("%Y%m%d")
genomes_folder = "genomes"
new_phage_list_url = 'http://phagesdb.org/data/unphameratedlist'
pecaan_prefix = 'https://discoverdev.kbrinsgd.org/phameratoroutput/phage/'

#You have to specify how many results to return at once. If you set it to 1 page long and 100,000 genomes/page, then this will return everything
sequenced_phages_url = "http://phagesdb.org/api/sequenced_phages/?page=1&page_size=100000"




#Define several functions

#Print out statements to both the terminal and to the output file
def write_out(filename,statement):
    print statement
    filename.write(statement)


#For questionable data, user is requested to clarify if the data is correct or not
def question(message):
    number = -1
    while number < 0:
        value = raw_input("Is this correct? (yes or no): ")
        if (value.lower() == "yes" or value.lower() == "y"):
            number = 0
        elif (value.lower() == "no" or value.lower() == "n"):                         
            write_out(report_file,message)
            number = 1
        else:
            print "Invalid response."
    #This value will be added to the current error total. If 0, no error was encountered. If 1, an error was encountered.
    return number
            
#Exits MySQL
def mdb_exit(message):
    write_out(report_file,"\nError: " + `sys.exc_info()[0]`+ ":" +  `sys.exc_info()[1]` + "at: " + `sys.exc_info()[2]`)
    write_out(report_file,message)
    write_out(report_file,"\nThe import script did not complete.")
    write_out(report_file,"\nExiting MySQL.")
    cur.execute("ROLLBACK")
    cur.execute("SET autocommit = 1")
    cur.close()
    con.close()
    write_out(report_file,"\nExiting import script.")
    sys.exit(1)


#Allows user to select which retrieval/update options to perform
def select_option(message):
    response = "no"
    response_valid = False
    while response_valid == False:
        response = raw_input(message)
        if (response.lower() == "yes" or response.lower() == "y"):
            response  = "yes"
            response_valid = True
        elif (response.lower() == "no" or response.lower() == "n"):                         
            response = "no"
            response_valid = True
        else:
            print "Invalid response."   
    return response











#Retrieve current data in database
#0 = PhageID
#1 = Name
#2 = HostStrain
#3 = status
#4 = Cluster
#5 = DateLastModified
#6 = Accession
#7 = RetrieveRecord
try:
    con = mdb.connect(mysqlhost, username, password, database)
    con.autocommit(False)
    cur = con.cursor()
except:
    print "Unsuccessful attempt to connect to the database. Please verify the database, username, and password."
    import_table_file.close()
    report_file.close()
    sys.exit(1)

try:
    cur.execute("START TRANSACTION")
    cur.execute("SELECT version FROM version")
    db_version = str(cur.fetchone()[0])
    cur.execute("SELECT PhageID,Name,HostStrain,status,Cluster,DateLastModified,Accession,RetrieveRecord FROM phage")
    current_genome_data_tuples = cur.fetchall()
    cur.execute("COMMIT")
    cur.close()
    con.autocommit(True)

except:
    import_table_file.close()
    report_file.close()
    mdb_exit("\nUnable to access the database to retrieve genome information.\nNo changes have been made to the database.")

con.close()



















#Determine which type of updates will be performed.
retrieve_field_updates = select_option("\nDo you want to retrieve Host and Cluster updates? (yes or no) ")
retrieve_phagesdb_genomes = select_option("\nDo you want to retrieve manually-annotated genomes from phagesdb? (yes or no) ")
retrieve_pecaan_genomes = select_option("\nDo you want to retrieve auto-annotated genomes from PECAAN? (yes or no) ")
retrieve_ncbi_genomes = select_option("\nDo you want to retrieve updated NCBI records? (yes or no) ")

if retrieve_ncbi_genomes == "yes":
    #Get email infor for NCBI
    contact_email = raw_input("Provide email for NCBI: ")






#Create all appropriate output directories
#Different folder for each type of update
#Within each folder, a genomes folder is created to stored only new genome files
#Create all appropriate import table files
if retrieve_field_updates == "yes":


    #Output folder
    field_updates_folder = '%s_field_updates' % date
    field_updates_path = os.path.join(updateFileDir,field_updates_folder)


    try:
        os.mkdir(field_updates_path)
    except:
        print "\nUnable to create output folder: %s" % field_updates_path
        sys.exit(1)
        
    #This is a dummy folder, since the comparison script does not retrieve any files.
    #However, creating the folder makes it easier to run the import_script on the corrections_import_table, since this script relies on the presence of a genomes folder.
    os.mkdir(os.path.join(field_updates_path,genomes_folder))


    #Import table
    field_import_table_handle = open(os.path.join(comparison_output_path,date + "_field_update_import_table.csv"), "w")
    field_import_table_writer = csv.writer(field_import_table_handle)


if retrieve_phagesdb_genomes == "yes":

    #Output folder
    phagesdb_output_folder = '%s_retrieved_phagesdb_flatfiles' % date
    phagesdb_output_path = os.path.join(updateFileDir,phagesdb_output_folder)

    try:
        os.mkdir(phagesdb_output_path)
    except:
        print "\nUnable to create output folder: %s" %phagesdb_output_path
        sys.exit(1)
    os.chdir(phagesdb_output_path)

    #Genomes folder
    os.mkdir(os.path.join(phagesdb_output_folder,genomes_folder))

    #Import table
    phagesdb_import_table_handle = open(os.path.join(phagesdb_output_path,date + "_phagesdb_import_table.csv"), "w")
    phagesdb_import_table_writer = csv.writer(phagesdb_import_table_handle)


if retrieve_pecaan_genomes == "yes":


    #Output folder
    pecaan_output_folder = '%s_retrieved_pecaan_flatfiles' % date
    pecaan_output_path = os.path.join(updateFileDir,pecaan_output_folder)

    try:
        os.mkdir(pecaan_output_path)
    except:
        print "\nUnable to create output folder: %s" %pecaan_output_path
        sys.exit(1)

    #Genomes folder
    os.mkdir(os.path.join(pecaan_output_path,genomes_folder))

        
    #Import table
    pecaan_import_table_handle = open(os.path.join(pecaan_output_path,date + "_pecaan_import_table.csv"), "w")
    pecaan_import_table_writer = csv.writer(pecaan_import_table_handle)


if retrieve_ncbi_genomes == "yes":

    #Output folder
    ncbi_output_folder = '%s_retrieved_ncbi_flatfiles' % date
    ncbi_output_path = os.path.join(updateFileDir,ncbi_output_folder)

    try:
        os.mkdir(ncbi_output_path)
    except:
        print "\nUnable to create output folder: %s" % ncbi_output_path
        sys.exit(1)


    #Genomes folder
    os.mkdir(os.path.join(ncbi_output_path,genomes_folder))

        
    #Import table
    ncbi_import_table_handle = open(os.path.join(ncbi_output_path,date + "_ncbi_import_table.csv"), "w")
    ncbi_import_table_writer = csv.writer(ncbi_import_table_handle)


    #Processing results file
    ncbi_results_handle = open(os.path.join(ncbi_output_path,date + "_ncbi_results.csv","w")
    ncbi_results_writer = csv.writer(ncbi_results_handle)
    ncbi_results_headers = ['PhageID','PhageName','Accession','Status','PhameratorDate','RetrievedRecordDate','Result']
    ncbi_results_writer.writerow(ncbi_results_headers)






























#Option 1: Retrieve Host and Cluster updates from phagesdb
#Option 2: Retrieve Genbank-formatted files (both SMART QC and any other new annotation) from phagesdb

if (retrieve_field_updates == "yes" or retrieve_phagesdb_genomes == "yes"):


    print "\n\nRetrieving updated Host and Cluster data and/or retrieving new manually-annotated files from phagesdb"



    if retrieve_phagesdb_genomes == "yes":
 
        #Initialize phagesdb retrieval variables 
        phagesdb_retrieved_tally = 0
        phagesdb_failed_tally = 0
        phagesdb_retrieved_list = []
        phagesdb_failed_list = []

 
        
    #Variable to track number of warnings and total_errors encountered
    warnings = 0
    total_errors = 0

    #Create data sets
    phamerator_id_set = set()
    phamerator_name_set = set()
    phamerator_host_set = set()
    phamerator_status_set = set()
    phamerator_cluster_set = set()
    phamerator_accession_set = set()
    print "Preparing genome data sets from the phamerator database..."
    
    modified_genome_data_list = []
    phamerator_duplicate_accessions = []
    for genome_tuple in current_genome_data_tuples:


        phamerator_id = genome_tuple[0]
        phamerator_name = genome_tuple[1]
        phamerator_host = genome_tuple[2]
        phamerator_status = genome_tuple[3]
        phamerator_cluster = genome_tuple[4]
        phamerator_date = genome_tuple[5]
        phamerator_accession = genome_tuple[6]
        phamerator_retrieve = genome_tuple[7]




        #In Phamerator, Singleton Clusters are recorded as '\N', but in phagesdb they are recorded as "Singleton"
        if phamerator_cluster is None:
            phamerator_cluster = 'Singleton'


        #Accession data may have version number (e.g. XY12345.1)
        if phamerator_accession != "":
            phamerator_accession = phamerator_accession.split('.')[0]

        #Check for accession duplicates            
        if phamerator_accession in phamerator_accession_set:
            phamerator_duplicate_accessions.append(phamerator_accession)
        else:
            phamerator_accession_set.add(phamerator_accession)




        modified_genome_data_list.append([phamerator_id,\
                                            phamerator_name,\
                                            phamerator_host,\
                                            phamerator_status,\
                                            phamerator_cluster,\
                                            phamerator_date,\
                                            phamerator_accession,\
                                            phamerator_retrieve]
    
    
    
    for genome_tuple in current_genome_data_tuples:

    

    if len(phamerator_duplicate_accessions) > 0:
        print "There are duplicate in accessions Phamerator. Unable to proceed with NCBI record retrieval."
        for accession in phamerator_duplicate_accessions:
            print accession
        raw_input("Press ENTER to proceed")
        sys.exit(1)

    
    
    for genome_tuple in current_genome_data_tuples:
        phamerator_id_set.add(genome_tuple[0])
        phamerator_name_set.add(genome_tuple[1])
        phamerator_host_set.add(genome_tuple[2])
        phamerator_cluster_set.add(genome_tuple[4])




    #phagesdb relies on the phageName, and not the phageID. But Phamerator does not require phageName values to be unique.
    #Check if there are any phageName duplications. If there are, they will not be able to be compared to phagesdb data.
    if len(phamerator_id_set) != len(phamerator_name_set):
        print "There appears to be duplicate phageNames in Phamerator. Data is not able to be matched to phagesdb."
        total_errors += question("\nError: phageNames are not unique")
        
        
       
    #Retrieve a list of all sequenced phages listed on phagesdb
    sequenced_phages_json = urllib.urlopen(sequenced_phages_url)
    sequenced_phages_dict = json.loads(sequenced_phages_json.read())
    sequenced_phages_json.close()

    #Data for each phage is stored in a dictionary per phage, and all dictionaries are stored in the "results" list
    phagesdb_data_dict = {}
    for element_dict in sequenced_phages_dict["results"]:
        print element_dict["phage_name"]
        phagesdb_data_dict[element_dict["phage_name"]] = element_dict
        
        
    if (len(sequenced_phages_dict["results"]) != sequenced_phages_dict["count"] or len(sequenced_phages_dict["results"]) != len(phagesdb_data_dict)):
        write_out(report_file,"\nError: not all phage data retrieved from phagesdb. Change default parameters in script to proceed.")
        total_errors += 1
        sys.exit()
        
        
        
    #Now that all phagesdb data retrieved, match up to Phamerator data

    matched_count = 0
    unmatched_count = 0
    unmatched_phage_id_list = []

    #Iterate through each phage in Phamerator
    for genome_tuple in current_genome_data_tuples:



        field_corrections_needed = 0

        phamerator_id = genome_tuple[0]
        phamerator_name = genome_tuple[1]
        phamerator_host = genome_tuple[2]
        phamerator_status = genome_tuple[3]
        phamerator_cluster = genome_tuple[4]
        phamerator_date = genome_tuple[5]
        phamerator_accession = genome_tuple[6]
        phamerator_retrieve = genome_tuple[7]

                    
        #Ensure the phageID does not have Draft appended    
        if phamerator_id[-6:].lower() == "_draft":
            phage_id_search_name = phamerator_id[:-6]
        else:
            phage_id_search_name = phamerator_id

        #Ensure the phage name does not have Draft appended    
        if phamerator_name[-6:].lower() == "_draft":
            phage_name_search_name = phamerator_name[:-6]
        else:
            phage_name_search_name = phamerator_name   


        #First try to match up the phageID, and if that doesn't work, try to match up the phageName
        if phage_id_search_name in phagesdb_data_dict.keys():
            matched_phagesdb_data = phagesdb_data_dict[phage_id_search_name]
            matched_count += 1
      
        elif phage_name_search_name in phagesdb_data_dict.keys():
            matched_phagesdb_data = phagesdb_data_dict[phage_name_search_name]
            matched_count += 1

        else:
            write_out(report_file,"\nError: unable to find phageID %s or phageName %s from phagesdb." %(phamerator_id,phamerator_name))
            matched_phagesdb_data = ""
            unmatched_count += 1
            unmatched_phage_id_list.append(phamerator_id)
            continue


        #Matched name and host
        phagesdb_name = matched_phagesdb_data['phage_name']
        phagesdb_host = matched_phagesdb_data['isolation_host']['genus']


        #Matched cluster
        if matched_phagesdb_data['pcluster'] is None:
            #Sometimes cluster information is not present. In the phagesdb database, it is is recorded as NULL.
            #When phages data is downloaded from phagesdb, NULL cluster data is converted to "Unclustered".
            #In these cases, leaving the cluster as NULL in phamerator won't work, because NULL means Singleton. Therefore, the phamerator cluster is listed as 'UKN' (Unknown). 
            phagesdb_cluster = 'UKN'

        else: 
            phagesdb_cluster = matched_phagesdb_data['pcluster']['cluster']


        #Matched subcluster
        if matched_phagesdb_data['psubcluster'] is None:
            #If a phage has a cluster, but not a subcluster, set subcluster to Unspecified
            phagesdb_subcluster = 'Unspecified'
        
        else:
            phagesdb_subcluster = matched_phagesdb_data['psubcluster']['subcluster']



        #Determine if any fields need updated
        if retrieve_field_updates == "yes":

            #If the Host and/or cluster data needs updated in Phamerator, decide what the value will be to update the Cluster data.
            if phagesdb_subcluster == 'Unspecified':
                phagesdb_cluster_update = phagesdb_cluster
            else:
                phagesdb_cluster_update = phagesdb_subcluster
             
            #Compare Cluster and Subcluster
            if phagesdb_subcluster == 'Unspecified':
            
                if phamerator_cluster != phagesdb_cluster:
                    print "\nError: Phamerator Cluster %s does not match with phagesdb Cluster %s for phageID %s." %(phamerator_cluster,phagesdb_cluster,phamerator_id)
                    field_corrections_needed += 1
                
            elif phamerator_cluster != phagesdb_subcluster:
                    print "\nError: Phamerator Cluster %s does not match with phagesdb Subcluster %s for phageID %s." %(phamerator_cluster,phagesdb_subcluster,phamerator_id)
                    field_corrections_needed += 1

            #Compare Host genus
            if phamerator_host != phagesdb_host:
                print "\nPhamerator host %s and phagesdb host %s do not match for phageID %s." %(phamerator_host,phagesdb_host,phamerator_id)
                field_corrections_needed += 1


            #If errors in the Host or Cluster information were identified, create an import ticket to for the import script to implement.
            if field_corrections_needed > 0:
                field_import_table_writer.writerow(["update",phamerator_id,phagesdb_host,phagesdb_cluster_update,phamerator_status,"none","none"])
        
              




        #Determine if any new Genbank-formatted files are available
        if retrieve_phagesdb_genomes == "yes":
        
        
            #Retrieve the qced_genbank_file_date data and properly format it.
            #Some phages may have a file but no associated date tagged with that file (since date tagging has only recently been implemented).        
            #If there is no date, it is Null. If there is a date, it is formatted as: '2017-02-15T10:37:21Z'
            phagesdb_flatfile_date = phagesdb_data_dict["qced_genbank_file_date"]

            if phagesdb_flatfile_date is None:                

                phagesdb_flatfile_date = datetime.strptime('1/1/1900','%m/%d/%Y')
                
            else:
                
                phagesdb_flatfile_date = phagesdb_flatfile_date.split('T')[0]
                phagesdb_flatfile_date = datetime.strptime(phagesdb_flatfile_date,'%Y-%m-%d')


            #Not all phages have associated Genbank-formatted files available on phagesdb.
            #Check to see if there is a flatfile for this phage.
            #Download the flatfile only if there is a date tag, and only if that date is more recent than the date stored in Phamerator for that genome.
            #The tagged date only reflects when the file was uploaded into phagesdb. The date the actual Genbank record was created is stored within the file,
            #and this too could be less recent than the current version in Phamerator; however, this part gets checked during the import stage.


            if (phagesdb_data_dict["qced_genbank_file"] is None or not phagesdb_flatfile_date > phamerator_date):

                print "No flatfile is available that is more recent than current phamerator version for phageID %s." % phamerator_id
                phagesdb_failed_tally += 1
                phagesdb_failed_list.append(phamerator_id)

            else:

                #Save the file on the hard drive with the same name as stored on phagesdb
                phagesdb_flatfile_url = phagesdb_data_dict["qced_genbank_file"]
                phagesdb_file = phagesdb_flatfile_url.split('/')[-1]
               
                try:
                    phagesdb_flatfile_response = urllib2.urlopen(phagesdb_flatfile_url)
                    phagesdb_file_handle = open(phagesdb_file,'w')
                    phagesdb_file_handle.write(phagesdb_flatfile_response.read())
                    flatfile_response.close()
                    phagesdb_file_handle.close()
                    
                    
                    #Create the new import ticket
                    import_table_writer.writerow(["replace",phage_id_search_name,"retrieve","retrieve","final","product",phamerator_id])

                    retrieved_tally += 1
                    retrieved_list.append(phamerator_id)

                except:
                    print "Error: unable to retrieve or read flatfile for phageID %s." %phamerator_id
                    failed_tally += 1
                    failed_list.append(phamerator_id)




    #Report retrieval results
    if retrieved_tally > 0:
        print "\n\nThe following %s phage(s) were successfully retrieved:" %retrieved_tally
        for element in retrieved_list:
            print element
    else:
        print "No new flatfiles available."


    if failed_tally > 0:
        print "\n\nThe following %s phage(s) failed to be retrieved:" %failed_tally
        for element in failed_list:
            print element
    else:
        print "No phages failed to be retrieved."
        



    print "\nMatched phage tally: %s." %matched_count
    print "\nUnmatched phage tally: %s." %unmatched_count
    print "\nUnmatched phages:"
    for element in unmatched_phage_id_list:
        print element












#Option 2: Retrieve auto-annotated genomes from PECAAN
if retrieve_pecaan_genomes == "yes":

    print "\n\nRetrieving new phages from PECAAN"


    #Retrieve list of unphamerated genomes
    #Retrieved file should be tab-delimited text file, each row is a newly sequenced phage
    phagesdb_response = urllib2.urlopen(new_phage_list_url)





    #Retrieve auto-annotated genomes from PECAAN
    retrieved_tally = 0
    failed_tally = 0
    retrieved_list = []
    failed_list = []


    #Iterate through each row in the file
    for new_phage in phagesdb_response:


        #PECAAN should be able to generate any phage that is listed on phagesdb
        new_phage = new_phage.strip() #Remove \t character at the end of each row
        pecaan_link = pecaan_prefix + new_phage
        pecaan_file = new_phage + "_Draft.txt"
        #print pecaan_link
        try:
            pecaan_response = urllib2.urlopen(pecaan_link)
            pecaan_file_handle = open(pecaan_file,'w')
            pecaan_file_handle.write(pecaan_response.read())
            pecaan_response.close()
            pecaan_file_handle.close()
            
            
            #Create the new import ticket
            import_table_writer.writerow(["add",new_phage,"retrieve","retrieve","draft","product","none"])
            print "Retrieved %s from PECAAN." %new_phage
            retrieved_tally += 1
            retrieved_list.append(new_phage)

        except:
            print "Error: unable to retrieve %s draft genome." %new_phage
            failed_tally += 1
            failed_list.append(new_phage)


    phagesdb_response.close()


    #Report results
    if retrieved_tally > 0:
        print "The following %s phage(s) were successfully retrieved:" %retrieved_tally
        for element in retrieved_list:
            print element
    else:
        print "No new draft genomes available."


    if failed_tally > 0:
        print "The following %s phage(s) failed to be retrieved:" %failed_tally
        for element in failed_list:
            print element
    else:
        print "No phages failed to be retrieved."


    print "\nDone retrieving auto-annotated genomes from PECAAN.\n\n\n"
    import_table_file.close()
    os.chdir('..')













    
    
    
    


#Option 4: Retrieve updated records from NCBI

if retrieve_ncbi_genomes == "yes":


    #Flow of the NCBI record retrieval process:
    #1 Create list of phages to check for updates at NCBI
    #2 Using esearch, verify the accessions are valid
    #3 Retrieve valid records in batches
    #4 Check which records are newer than the upload date of the current version in phamerator
    #5 Save new records in a folder and create an import table for them

    print "\n\nRetrieving updated records from NCBI"


    batch_size = ""
    batch_size_valid = False
    while batch_size_valid == False:
        batch_size = raw_input("Record retrieval batch size (must be greater than 0 and recommended is 100-200): ")
        print "\n\n"
        if batch_size.isdigit():
            batch_size = int(batch_size)
            if batch_size > 0:
                batch_size_valid = True
            else:
                print "Invalid choice."
                print "\n\n"

        else:
            print "Invalid choice."
            print "\n\n"








    #Initialize tally variables
    tally_total = 0
    tally_not_updated = 0
    tally_no_accession = 0
    tally_duplicate_accession = 0
    tally_retrieval_failure = 0
    tally_retrieved_not_new = 0
    tally_retrieved_for_update = 0
    tally_total = len(current_genome_data_tuples)






    #Create dictionary of phage data based on unique accessions
    #Key = accession
    #Value = phage data list
    #Create list of phage data with duplicate accession info
    unique_accession_dict = {}
    duplicate_accession_list = []

    phamerator_accession_set = set()
    phamerator_duplicate_accessions = []
    for genome_tuple in current_genome_data_tuples:
    
        if genome_tuple[6] != "":
        
            if genome_tuple[6] in phamerator_accession_set:
                phamerator_duplicate_accessions.append(genome_tuple[6])
            else:
                phamerator_accession_set.add(genome_tuple[6].split('.')[0])

    if len(phamerator_duplicate_accessions) > 0:
        print "There are duplicate in accessions Phamerator. Unable to proceed with NCBI record retrieval."
        for accession in phamerator_duplicate_accessions:
            print accession
        raw_input("Press ENTER to proceed")
        sys.exit(1)


    #Add to dictionary if 1) the genome is set to be automatically updated and 2) if there is an accession number
    for genome_tuple in current_genome_data_tuples:

        phamerator_id = genome_tuple[0]
        phamerator_name = genome_tuple[1]
        phamerator_host = genome_tuple[2]
        phamerator_status = genome_tuple[3]
        phamerator_cluster = genome_tuple[4]
        phamerator_date = genome_tuple[5]
        phamerator_accession = genome_tuple[6]
        phamerator_retrieve = genome_tuple[7]

        
        
        #Edit some of the phage data fields    
        #When querying NCBI with Accession numbers, efetch retrieves the most updated version. So you can drop the version number after the decimal (e.g. 'XY99999.1')
        if phamerator_accession != "":
            phamerator_accession = phamerator_accession.split('.')[0]


        #Singleton Cluster values should be converted from None to 'Singleton'
        if phamerator_cluster is None:
            phamerator_cluster = "Singleton"
            print "PhageID %s Cluster converted to Singleton." %phamerator_cluster


        #Make sure there is a date in the DateLastModified field
        if phamerator_date is None:
            phamerator_date = datetime.strptime('1/1/1900','%m/%d/%Y')


        #Now determine what to do with the data
        #Since some fields have been modified, you can't pass the original genome_tuple to the duplicate accession list of unique accession dictionary
        if phamerator_retrieve != 1:
            print "PhageID %s is not set to be automatically updated by NCBI record." %phamerator_id
            tally_not_updated += 1
            processing_results_file_writer.writerow([phamerator_id,phamerator_name,phamerator_accession,phamerator_status,phamerator_date,'NA','no automatic update'])

        elif phamerator_accession == "" or phamerator_accession is None:
            print "PhageID %s is set to be automatically update, but it does not have accession number." %phamerator_id
            tally_no_accession += 1
            processing_results_file_writer.writerow([phamerator_id,phamerator_name,phamerator_accession,phamerator_status,phamerator_date,'NA','no accession'])
        
        else:
            unique_accession_dict[phamerator_accession] = [phamerator_id,phamerator_name,phamerator_host,phamerator_status,phamerator_cluster,phamerator_date,phamerator_accession,phamerator_retrieve]




        



    #2 & #3 Use esearch to verify the accessions are valid and efetch to retrieve the record
    Entrez.email = contact_email
    Entrez.tool = "NCBIRecordRetrievalScript"



    #Create batches of accessions
    unique_accession_list = unique_accession_dict.keys()

    #Add [ACCN] field to each accession number
    index = 0
    while index < len(unique_accession_list):
        unique_accession_list[index] = unique_accession_list[index] + "[ACCN]"
        index += 1


    retrieved_record_list = []
    retrieval_error_list = []



    #When retrieving in batch sizes, first create the list of values indicating which indices of the unique_accession_list should be used to create each batch
    #For instace, if there are five accessions, batch size of two produces indices = 0,2,4
    for batch_index_start in range(0,len(unique_accession_list),batch_size):

        
        if batch_index_start + batch_size > len(unique_accession_list):
            batch_index_stop = len(unique_accession_list)
        else:
            batch_index_stop = batch_index_start + batch_size
        
        current_batch_size = batch_index_stop - batch_index_start        
        delimiter = " | "
        esearch_term = delimiter.join(unique_accession_list[batch_index_start:batch_index_stop])


        #Use esearch for each accession
        search_handle = Entrez.esearch(db = "nucleotide", term = esearch_term,usehistory="y")
        search_record = Entrez.read(search_handle)
        search_count = int(search_record["Count"])
        search_webenv = search_record["WebEnv"]
        search_query_key = search_record["QueryKey"]


        
        #Keep track of the accessions that failed to be located in NCBI
        if search_count < current_batch_size:
            search_accession_failure = search_record["ErrorList"]["PhraseNotFound"]

            #Each element in this list is formatted "accession[ACCN]"
            for element in search_accession_failure:
                retrieval_error_list.append(element[:-6])
        
        
        
        #Now retrieve all records using efetch
        fetch_handle = Entrez.efetch(db = "nucleotide", rettype = "gb", retmode = "text", retstart = 0,retmax = search_count, webenv = search_webenv,query_key = search_query_key)
        fetch_records = SeqIO.parse(fetch_handle,"genbank")

        for record in fetch_records:
            retrieved_record_list.append(record)

        search_handle.close()
        fetch_handle.close()



    #4 Now that all records have been retrieved, check which records are newer than the upload date of the current version in phamerator.
    # Create the genbank-formatted file only if it is a newer genome
    # Also create an import table
    import_table_file = open(os.path.join(ncbi_output_path,date + "_ncbi_import_table.csv"), "w")
    import_table_file_writer = csv.writer(import_table_file)


    #Create the output folder to hold the genome files
    os.mkdir(genomes_folder)
    os.chdir(genomes_folder)



    tally_retrieval_failure = len(retrieval_error_list)
    for retrieval_error_accession in retrieval_error_list:

        phamerator_data = unique_accession_dict[retrieval_error_accession]
        processing_results_file_writer.writerow([phamerator_data[0],phamerator_data[1],phamerator_data[5],phamerator_data[4],phamerator_data[6],'NA','retrieval failure'])




    for retrieved_record in retrieved_record_list:
        retrieved_record_accession = retrieved_record.name

        #Convert date date to datetime object
        retrieved_record_date = retrieved_record.annotations["date"]
        retrieved_record_date = datetime.strptime(retrieved_record_date,'%d-%b-%Y')


        #MySQL outputs the DateLastModified as a datetime object
        phamerator_data = unique_accession_dict[retrieved_record_accession]

        #5 Save new records in a folder and create an import table row for them
        if retrieved_record_date > phamerator_data[6]:

            print 'Retrieved record date %s is more recent than phamerator date %s.' %(retrieved_record_date,phamerator_data[6])
            tally_retrieved_for_update += 1
            processing_results_file_writer.writerow([phamerator_data[0],phamerator_data[1],phamerator_data[5],phamerator_data[4],phamerator_data[6],retrieved_record_date,'update record'])


            #Now output genbank-formatted file to be uploaded to Phamerator and create the import table action
            #First remove the "_Draft" suffix if it is present
            if phamerator_data[0][-6:].lower() == '_draft':
                import_table_name = phamerator_data[0][:-6]
            else:
                import_table_name = phamerator_data[0]
            
            SeqIO.write(retrieved_record, phamerator_data[1].lower() + "__" + retrieved_record_accession + ".gb","genbank")
            import_table_data_list = ['replace',import_table_name,phamerator_data[2],phamerator_data[3],'final','product',phamerator_data[0]]
            import_table_file_writer.writerow(import_table_data_list)


        else:
            print 'Phamerator date %s is more recent than retrieved record date %s.' %(phamerator_data[6],retrieved_record_date)
            tally_retrieved_not_new += 1
            processing_results_file_writer.writerow([phamerator_data[0],phamerator_data[1],phamerator_data[5],phamerator_data[4],phamerator_data[6],retrieved_record_date,'record not new'])        
            


    #Print summary of script
    print "Number of genomes in Phamerator: %s" %tally_total
    print "Number of genomes that are NOT set to be updated: %s" %tally_not_updated
    print "Number of auto-updated genomes with no accession: %s" %tally_no_accession
    print "Number of duplicate accessions: %s" %tally_duplicate_accession
    print "Number of records that failed to be retrieved: %s" %tally_retrieval_failure
    print "Number of records retrieved that are NOT more recent than Phamerator record: %s" %tally_retrieved_not_new
    print "Number of records retrieved that should be updated in Phamerator: %s" %tally_retrieved_for_update


    processing_check = tally_total - tally_not_updated - tally_no_accession - tally_duplicate_accession - tally_retrieval_failure - tally_retrieved_not_new - tally_retrieved_for_update
    if processing_check != 0:
        print "Processing check: %s" %processing_check
        print "Error: the processing of phages was not tracked correctly."
        print "\n\n\n"



    print "\nDone retrieving updated records from NCBI.\n\n\n"
    import_table_file.close()
    processing_results_file_handle.close()
    os.chdir('..')









    
    
####Close script.
print "\n\n\nRetrieve updates script completed."  

    report_file.close()
    import_table_file.close()    

            phage_file_handle.close()
            import_table_file.close()        















