#!/usr/bin/env python3

# Copyright (c) 2021, Malte Bjørn Hallgren Technical University of Denmark
# All rights reserved.
#
import sys
import os
import argparse
import operator
import random
import subprocess
import time
import gc
import numpy as np
import array
from optparse import OptionParser
from operator import itemgetter
import re
import json
import sqlite3
import moss_functions as moss
import mbh_helpers as mbh_helper
import moss_sql as moss_sql
import json
import datetime
import threading
import geocoder

#Note: these parser arguments are NOT meant to be user friendly as terminal commands. They are built to be automatically called from the ELectron Client.
parser = argparse.ArgumentParser(description='.')
parser.add_argument('-seqType', action="store", type=str, dest='seqType', default="", required=True, help='Should be either nanopore, se_illumina or pe_illumina.')
parser.add_argument("-prune_distance", type=int, action="store", dest="prune_distance", default=10, help="X lenght that SNPs can be located between each other. Default is 10. If two SNPs are located within X lenght of eachother, everything between them as well as X lenght on each side of the SNPs will not be used in the alignments to calculate the distance matrix.")
parser.add_argument("-bc", action="store", type=float, default = 0.7, dest="bc", help="Base calling parameter for nanopore KMA mapping. Default is 0.7")
parser.add_argument("-db_dir", action="store", type=str, default = "", dest="db_dir", help="Comeplete path to the database directory generated by running moss.py. Default name is db_dir.")
parser.add_argument("-laptop", action="store_true", default = False, dest="laptop", help="when using a laptop - DB not loaded to shm")
parser.add_argument("-thread", action="store", default = 1, dest="multi_threading", help="Set this parameter to x-number of threads that you would like to use during KMA-mapping.")
parser.add_argument('-version', action='version', version='MOSS 1.0.0')
parser.add_argument("-exepath", action="store", dest="exepath", default = "", help="Complete path to the moss repo that you cloned, in which your kma and ccphylo folder at located.")
parser.add_argument("-metadata", action="store", dest="metadata", default = "", help="metadata")
parser.add_argument("-metadata_headers", action="store", dest="metadata_headers", default = "", help="metadata_headers")

args = parser.parse_args()

jobid = random.randint(1,100000000)

def moss_pipeline(seqType, prune_distance, bc,
                         db_dir, multi_threading, exepath, laptop, metadata, metadata_headers):


    db_dir = moss.correctPathCheck(db_dir)
    exepath = moss.correctPathCheck(exepath)
    
    metadata_dict = moss.prod_metadata_dict(metadata, metadata_headers)
    input = metadata_dict['input'].split()

    start_time = datetime.datetime.now()

    if metadata_dict['latitude'] == '' or metadata_dict['longitude'] == '':
        latitude, longitude = moss.calc_coordinates_from_location(metadata_dict['city'], metadata_dict['country'])
        metadata_dict['latitude'] = latitude
        metadata_dict['longitude'] = longitude

    inputType, total_filenames, assemblyType = moss.mossCheckInputFiles(input, seqType)


    if inputType == "nanopore" or inputType == "se_illumina":
        samplename = input[0].split("/")[-1]
        entryid = moss.md5(input[0])
    elif inputType == "pe_illumina":
        samplename = input[0].split("/")[-1]
        illumina_name1 = input[0].split("/")[-1]
        illumina_name2 = input[1].split("/")[-1]
        entryid = moss.md5(input[0])

    moss.uniqueNameCheck(db_dir, inputType, total_filenames)

    moss_sql.init_status_table(entryid, "Initializing", "Not Determined", "1", "10", "Running", db_dir)
    moss_sql.init_isolate_table(entryid, "", samplename, "", "", "", db_dir)

    target_dir = db_dir + "analysis/" + entryid + "/"
    cmd = "mkdir " + target_dir
    os.system(cmd)
    kma_database_path = db_dir + "REFDB.ATG"

    logfilename = target_dir + "logfile_" + entryid
    logfile = open(logfilename, 'w')

    cmd = "mkdir " + target_dir + "datafiles"
    os.system(cmd)
    cmd = "mkdir " + target_dir + "datafiles/isolatefiles"
    os.system(cmd)

    startTime = time.time()
    mbh_helper.print_to_logfile("# input: {}".format(total_filenames), logfile, True)

    moss_sql.update_status_table(entryid, "CGE_finders", "Not Determined", "2", "10", "Running", db_dir)

    mbh_helper.print_to_logfile("# Running CGE tool: {}".format("Resfinder"), logfile, True)
    moss.runResFinder(exepath, total_filenames, target_dir, seqType)
    mbh_helper.print_to_logfile("# Running CGE tool: {}".format("PlasmidFinder"), logfile, True)
    moss.runPlasmidFinder(exepath, total_filenames, target_dir)
    mbh_helper.print_to_logfile("# Running CGE tool: {}".format("VirulenceFinder"), logfile, True)
    moss.runVirulenceFinder(exepath, total_filenames, target_dir)
    mbh_helper.print_to_logfile("# Running KMA mapping for template identification", logfile, True)

    best_template_score, template_found, header_text = moss.KMA_mapping(total_filenames, target_dir, kma_database_path, logfile, exepath + "kma/kma", laptop)
    mlst_result = moss.run_mlst(exepath, total_filenames, target_dir, header_text, seqType)

    moss_sql.update_status_table(entryid, "KMA Mapping", "Not Determined", "3", "10", "Running", db_dir)

    best_template = moss.findTemplateNumber(db_dir, header_text)

    mbh_helper.print_to_logfile("Best template number: {}".format(best_template), logfile, True)

    plasmid_count, plasmid_list = moss.plasmid_data_for_report(target_dir + "plasmidFinderResults/data.json",
                                                               target_dir)
    plasmid_string = ",".join(plasmid_list)
    virulence_count, virulence_list = moss.virulence_data_for_report(target_dir + "virulenceFinderResults/data.json",
                                                                     target_dir, logfile)
    virulence_string = ",".join(virulence_list)

    warning, riskcategory, allresgenes, amrinfo = moss.checkAMRrisks(target_dir, entryid, db_dir, header_text, exepath,
                                                                     logfile)

    moss_sql.update_isolate_table(entryid, header_text, samplename,
                                                    plasmid_string.replace("'", "''"),
                                                    allresgenes.replace(", ", ",").replace("'", "''"),
                                                    virulence_string.replace("'", "''"), db_dir)

    if best_template == None:
        template_found = False

    mbh_helper.print_to_logfile("Best template: {}".format(header_text), logfile, True)

    mbh_helper.print_to_logfile("Best template score: " + str(best_template_score), logfile, True)

    if template_found == False: #NO TEMPLATE FOUND #Being assembly
        associated_species = "No related reference identified, manual curation required. ID: {} name: {}".format(
            entryid, samplename)
        moss.run_assembly(entryid, db_dir, samplename, assemblyType, inputType, target_dir, input, illumina_name1,
                          illumina_name2, jobid, exepath, kma_database_path, start_time, logfile, ID, associated_species)

    moss_sql.update_status_table(entryid, "IPC check", "Alignment", "4", "10", "Running", db_dir)

    result, action = moss.acquire_semaphore("ipc_index_refdb", db_dir, 1, 7200)
    if result == 'acquired' and action == False:
        moss.release_semaphore("ipc_index_refdb", db_dir)
    elif result != 'acquired' and action == True:
        result += " : ipc_index_refdb"
        sys.exit(result)
    else:
        sys.exit('A semaphore related issue has occured. ipc_index_refdb update')

    print('mpr: true', file=logfile)

    if " " in header_text:
        templateaccesion = header_text.split(" ")[0]
    else:
        templateaccesion = header_text

    if inputType == "pe_illumina":
        moss.illuminaMappingPE(input, best_template, target_dir, kma_database_path, logfile, multi_threading, exepath + "kma/kma", templateaccesion, db_dir, laptop)
    elif inputType == "se_illumina":
        moss.illuminaMappingForward(input, best_template, target_dir, kma_database_path, logfile, multi_threading, exepath + "kma/kma", templateaccesion, db_dir, laptop)
    if inputType == "nanopore":
        moss.nanoporeMapping(input, best_template, target_dir, kma_database_path, logfile, multi_threading, bc, exepath + "kma/kma", templateaccesion, db_dir, laptop)

    conn = sqlite3.connect(db_dir + "moss.db")
    c = conn.cursor()

    print (header_text)

    c.execute("SELECT * FROM referencetable WHERE header_text = '{}'".format(header_text))
    print ("SELECT * FROM referencetable WHERE header_text = '{}'".format(header_text))
    refdata = c.fetchall()
    conn.close()

    header_text = refdata[0][5]


    related_isolates = moss.fetch_isolates(db_dir, header_text)

    moss_sql.update_status_table(entryid, "CCphylo", "Alignment", "5", "10", "Running", db_dir)

    #Here make function for tmp dir with isolates and consensus sequence and ref
    moss.make_phytree_output_folder(db_dir, target_dir, related_isolates, exepath, header_text)
    #TBD
    cmd = "{} dist -i {}/phytree_output/* -r \"{}\" -mc 0.01 -nm 0 -o {}/phytree_output/distance_matrix".format(exepath + "ccphylo/ccphylo", target_dir, header_text, target_dir)
    print (cmd, file = logfile)
    #Save latest newick to reference in SQL
    if prune_distance != 0 :
        cmd += " -pr {}".format(prune_distance)
    os.system(cmd)


    # Check if acceptable snp distance
    distance = moss.ThreshholdDistanceCheck("{}/phytree_output/distance_matrix".format(target_dir), header_text.split()[0]+".fsa", "{}{}_{}_consensus.fsa".format(target_dir, samplename, templateaccesion))
    print (distance, file = logfile)

    if distance > 300: #SNP distance
        header_text = header_text.split()
        associated_species = "{} {} assembly from ID: {}, SNP distance from best verified reference: {}".format(header_text[1], header_text[2], entryid, distance)
        moss.run_assembly(entryid, db_dir, samplename, assemblyType, inputType, target_dir, input, illumina_name1,
                          illumina_name2, jobid, exepath, kma_database_path, start_time, logfile, ID, associated_species)

    moss_sql.update_status_table(entryid, "Distance Matrix", "Alignment", "6", "10", "Running", db_dir)

    cmd = "{}ccphylo/ccphylo tree -i {}/phytree_output/distance_matrix -o {}/phytree_output/tree.newick".format(exepath, target_dir, target_dir)
    os.system(cmd)
    moss_sql.update_status_table(entryid, "Phylo Tree imaging", "Alignment", "7", "10", "Running", db_dir)

    image_location = moss.create_phylo_tree(db_dir, header_text, target_dir)

    if refdata[0][1] == '':
        isolateid = entryid
    else:
        isolateid = refdata[0][1] + ", " + entryid

    moss_sql.update_status_table(entryid, "Database updating", "Alignment", "8", "10", "Running", db_dir)

    moss_sql.update_reference_table(entryid, isolateid, None, None, None, header_text, db_dir)

    moss_sql.insert_amr_table(entryid, samplename, str(datetime.datetime.now())[0:-7], allresgenes.replace("'", "''"), amrinfo.replace("'", "''"), header_text, riskcategory.replace("'", "''"), warning.replace("'", "''"), db_dir)

    moss_sql.update_isolate_table(entryid, header_text, samplename, plasmid_string.replace("'", "''"), allresgenes.replace(", ", ",").replace("'", "''"), virulence_string.replace("'", "''"), db_dir)

    entries, values = moss.sql_string_metadata(metadata_dict)

    moss_sql.insert_metadata_table(entryid, entries, values, db_dir)

    new_plasmid_string, new_virulence_string, new_amr_string = moss.scan_reference_vs_isolate_cge(plasmid_string, allresgenes.replace(", ", ","), virulence_string, header_text, db_dir)

    moss_sql.update_reference_table(entryid, None, new_amr_string, new_virulence_string, new_plasmid_string, header_text, db_dir)

    end_time = datetime.datetime.now()
    run_time = end_time - start_time
    print("Run time: {}".format(run_time))
    print("Run time: {}".format(run_time), file=logfile)

    moss_sql.update_status_table(entryid, "Outbreak Finder", "Alignment", "9", "10", "Running", db_dir)



    cmd = "python3 {}src/outbreak_finder.py -db_dir {}".format(exepath, db_dir)
    os.system(cmd)

    moss_sql.update_status_table(entryid, "Alignment PDF compiling", "Alignment", "10", "10", "Running", db_dir)


    moss.compileReportAlignment(target_dir, entryid, db_dir, image_location, header_text, exepath) #No report compiled for assemblies! Look into it! #TBD

    logfile.close()
    moss_sql.update_status_table(entryid, "Alignment PDF compiling", "Alignment", "10", "10", "Finished", db_dir)



def main():
    moss_pipeline(args.seqType, args.prune_distance, args.bc, args.db_dir, args.multi_threading, args.exepath, args.laptop, args.metadata, args.metadata_headers)


if __name__== "__main__":
  main()
