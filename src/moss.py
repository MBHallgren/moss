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

import moss_sql as moss_sql
import json
import datetime
import threading
import geocoder

#Note: these parser arguments are NOT meant to be user friendly as terminal commands. They are built to be automatically called from the ELectron Client.
parser = argparse.ArgumentParser(description='.')
parser.add_argument("-config_name", action="store", type=str, default = "", dest="config_name", help="config_name.")
parser.add_argument('-version', action='version', version='MOSS 1.0.0')
parser.add_argument("-metadata", action="store", dest="metadata", default = "", help="metadata")
parser.add_argument("-metadata_headers", action="store", dest="metadata_headers", default = "", help="metadata_headers")

args = parser.parse_args()

def moss_pipeline(config_name, metadata, metadata_headers):
    start_time = datetime.datetime.now()

    config_name, metadata_dict, input, sample_name, entry_id, target_dir, ref_db, c_name = moss.moss_init(config_name, metadata, metadata_headers)
    moss.sql_execute_command("INSERT INTO sample_table(entry_id, sample_name, reference_id, amr_genes, virulence_genes, plasmids) VALUES('{}', '{}', '{}', '{}', '{}', '{}')"\
        .format(entry_id, sample_name, "", "", "", "", ""), config_name)


    moss.sql_execute_command("INSERT INTO status_table(entry_id, status, type, current_stage, final_stage, result, time_stamp) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
        entry_id, "Initializing", "Not determined", "1", "10", "Running", str(datetime.datetime.now())[0:-7],), config_name)

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\""\
                             .format("CGE finders", "Not Determined", "2", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    #moss.sql_execute_command("UPDATE status_table SET {}, {}, {}, {}, {}, {} WHERE {}".format(entry_id, "CGE finders", "Not Determined", "2", "10", "Running", config_name), config_name)


    moss.moss_mkfs(config_name, entry_id)

    #TBC FOR ALL FINDERS INSERT RELEVANT DATA INTO SQL
    # #add argument and check function TBD
    os.system("mkdir {}/finders".format(target_dir))
    moss.kma_finders("-ont -md 5 -1t1 -cge -apm", "resfinder", target_dir, input, "/opt/moss/resfinder_db/all")
    moss.kma_finders("-ont -md 5 -1t1 -cge -apm", "virulencefinder", target_dir, input, "/opt/moss/virulencefinder_db/all")
    moss.kma_finders("-ont -md 5 -1t1 -cge -apm", "resfinder_db", target_dir, input, "/opt/moss/resfinder_db/all")

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("KMA Mapping", "Not Determined", "3", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    #Rewrite this horrible kma_mapping function. Should be way simpler.
    template_score, template_search_result, reference_header_text, template_number = moss.kma_mapping(target_dir, input, config_name)

    associated_species = "{} - assembly from ID: {}".format(reference_header_text, entry_id)

    mlst_result = moss.run_mlst(input, target_dir, reference_header_text)

    #TBD INSERT FINDER RESULTS AND MLST INTO SQL SAMPLE TABLE

    #TBD NOT HERE, END OF PIPELINE, INSERT METADATA IN SAMPLE SQL FOR COMPLETED SAMPLES, BOTH ALIGNMENT AND ASSEMBLY

    if template_search_result == 1: #1 means error, thus no template found
        #Implement flye TBD later.
        moss.run_assembly(entry_id, config_name, sample_name, target_dir, input, reference_header_text,
                          associated_species)
    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("IPC check", "Alignment", "4", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    #Semaphores should be managed better tbh. Function within function?
    result, action = moss.acquire_semaphore("ipc_index_refdb", config_name, 1, 7200)
    if result == 'acquired' and action == False:
        moss.release_semaphore("ipc_index_refdb", config_name)
    elif result != 'acquired' and action == True:
        result += " : ipc_index_refdb"
        sys.exit(result)
    else:
        sys.exit('A semaphore related issue has occured. ipc_index_refdb update')

    #Dont manage SQL compatibility in mainscript. def variables earlier or in functions and return.
    if " " in reference_header_text:
        templateaccesion = reference_header_text.split(" ")[0]
    else:
        templateaccesion = reference_header_text

    consensus_name = "{}_{}_consensus".format(c_name, templateaccesion)

    moss.nanopore_alignment(input, template_number, target_dir, consensus_name, config_name)

    reference_id = moss.sql_fetch("SELECT entry_id FROM reference_table WHERE reference_header_text = '{}'".format(reference_header_text), config_name)[0][0]

    moss.sql_execute_command("UPDATE sample_table SET reference_id = '{}' WHERE entry_id = '{}'".format(reference_id, entry_id), config_name)

    #Managed in function when consensus in created ffs.
    cmd = "cp {}{}.fsa /opt/moss_db/{}/consensus_sequences/{}.fsa".format(target_dir, consensus_name, config_name, consensus_name)
    os.system(cmd)

    #Generic SQL query
    moss.sql_execute_command("UPDATE sample_table SET consensus_name = '{}.fsa' WHERE entry_id = '{}'".format(consensus_name, entry_id), config_name)

    related_isolates = moss.sql_fetch("SELECT consensus_name FROM sample_table WHERE reference_id = '{}'".format(reference_id), config_name)[0][0].split(",")

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("CCphylo", "Alignment", "5", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    #Fine, but can we include add ccphylo related in one function?
    moss.make_phytree_output_folder(config_name, target_dir, related_isolates, reference_header_text)

    #Why is cc phylo not in a function?
    cmd = "/opt/moss/ccphylo/ccphylo dist --input {}/phytree_output/* --reference \"{}\" --min_cov 0.01 --normalization_weight 0 --output {}/phytree_output/distance_matrix".format(target_dir, reference_header_text, target_dir)
    os.system(cmd)


    # Check if acceptable snp distance
    distance = moss.ThreshholdDistanceCheck("{}/phytree_output/distance_matrix".format(target_dir), reference_header_text.split()[0]+".fsa", consensus_name+".fsa")
    #Print in function ffs

    if distance > 300: #SNP distance
        #No associated species
        associated_species = "{} - assembly from ID: {}".format(reference_header_text, entry_id)
        moss.run_assembly(entry_id, config_name, sample_name, target_dir, input, reference_header_text,
                          associated_species)

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("Distance Matrix", "Alignment", "6", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    cmd = "/opt/moss/ccphylo/ccphylo tree --input {}/phytree_output/distance_matrix --output {}/phytree_output/tree.newick".format(target_dir, target_dir)
    os.system(cmd)

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("Phylo Tree imaging", "Alignment", "7", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    image_location = moss.create_phylo_tree(target_dir)

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("Database updating", "Alignment", "8", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("Compiling PDF", "Alignment", "9", "10", "Running", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)


    #moss.compileReportAlignment(target_dir, entry_id, config_name, image_location, reference_header_text, related_isolates) #No report compiled for assemblies! Look into it! #TBD

    sql_cmd = "UPDATE status_table SET status=\"{}\", type=\"{}\", current_stage=\"{}\", final_stage=\"{}\", result=\"{}\", time_stamp=\"{}\" WHERE entry_id=\"{}\"" \
        .format("Completed", "Alignment", "10", "10", "Completed", str(datetime.datetime.now())[0:-7], entry_id)
    moss.sql_execute_command(sql_cmd, config_name)

def main():
    moss_pipeline(args.config_name, args.metadata, args.metadata_headers)


if __name__== "__main__":
  main()
