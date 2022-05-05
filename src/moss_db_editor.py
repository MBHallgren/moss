#!/usr/bin/env python3

# Copyright (c) 2019, Malte Bjørn Hallgren Technical University of Denmark
# All rights reserved.
#

#Import Libraries

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
import json
from joblib import Parallel, delayed
#Use Argparse to correctly open the inputfiles

# Command tool for editing the Pathogen Real Time Typer database system.
# -Completely remove any isolate
# -Completely remove any reference
#       - Remove mapped isolates too, or analyse isolates?
#



parser = argparse.ArgumentParser(description='.')
parser.add_argument('-info', type=int, help='surveillance info')
parser.add_argument('-input_type', action="store", type=str, dest='input_type', default="", help='nanopore, se_illumina or pe_illumina')
parser.add_argument("-masking_scheme", type=str, action="store", dest="masking_scheme", default="", help="Give a fasta file containing a motof that you wish to mask in the aligned concensus files.")
parser.add_argument("-prune_distance", type=int, action="store", dest="prune_distance", default=5, help="X lenght that SNPs can be located between each other. Default is 10. If two SNPs are located within X lenght of eachother, everything between them as well as X lenght on each side of the SNPs will not be used in the alignments to calculate the distance matrix.")
parser.add_argument("-bc", action="store", type=float, default = 0.7, dest="bc", help="Base calling parameter for nanopore KMA mapping. Default is 0.7")
parser.add_argument("-config_name", action="store", type=str, default = "", dest="config_name", help="Comeplete path to the database directory generated by running moss.py. Default name is config_name.")
parser.add_argument("-thread", action="store", default = 1, dest="multi_threading", help="Set this parameter to x-number of threads that you would like to use during KMA-mapping.")
parser.add_argument("-o", action="store", dest="output_name", help="Name that you would like the output directory to be called.")
parser.add_argument('-version', action='version', version='moss 1.0.0', help = "Current version of PathogenRealTimeTyper.")
parser.add_argument("-exepath", action="store", dest="exepath", default = "", help="Complete path to the moss repo that you cloned, in which your kma and ccphylo folder at located.")
parser.add_argument("-parallel_input", action="store", dest="parallel_input", default = "", help="Comma seperated string containing complete paths to all input files.")
parser.add_argument("-jobs", type=int, action="store", dest="jobs", default = 4, help="Number of jobs to be run in parallel. Default is 4. Consider your computational capabilities!")
args = parser.parse_args()

def prrtAnalysis(input_type, inputlist, masking_scheme, prune_distance, bc, config_name, multi_threading, exepath, output_name, i):
    oneliner = "python3 {}moss.py".format(exepath)
    if input_type == "nanopore":
        oneliner += " -i_nanopore {}".format(inputlist[i])
    elif input_type == "se_illumina":
        oneliner += " -i_illumina {}".format(inputlist[i])
    elif input_type == "pe_illumina":
        oneliner += " -i_illumina {}".format(inputlist[i])

    if masking_scheme != "":
        oneliner += " -masking_scheme {}".format(masking_scheme)
    oneliner += " -bc {}".format(bc)
    oneliner += " -thread {}".format(multi_threading)
    oneliner += " -config_name {}".format(config_name)
    oneliner += " -exepath {}".format(exepath)
    oneliner += " -prune_distance {}".format(prune_distance)
    oneliner += " -o {}{}".format(output_name, i)
    os.system(oneliner)

def main(input_type, masking_scheme, prune_distance, bc, config_name, multi_threading, output_name, exepath, parallel_input, jobs):
    #LAV OMFATTENDE ERROR CHECK SÅ FRONT-END IKKE FEJLER
    cmd = "mkdir " + config_name + "multiSampleAnalysisReports/{}".format(output_name)
    os.system(cmd)
    cmd = "touch " + config_name + "multiSampleAnalysisReports/{}/stdout".format(output_name)
    os.system(cmd)
    cmd = "touch " + config_name + "multiSampleAnalysisReports/{}/stderr".format(output_name)
    os.system(cmd)

    print ("Currently a maximum of 8 jobs are permitted in parallel")
    if jobs > 8:
        sys.exit("Currently a maximum of 8 jobs are permitted in parallel")

    inputlist = parallel_input.split(",")
    Parallel(n_jobs=jobs)(delayed(prrtAnalysis)(input_type, inputlist, masking_scheme, prune_distance, bc, config_name, multi_threading, exepath, output_name, i) for i in range(len(inputlist)))
    print ("Analysis complete")

if __name__== "__main__":
  main(args.input_type, args.masking_scheme, args.prune_distance, args.bc, args.config_name, args.multi_threading, args.output_name, args.exepath, args.parallel_input, args.jobs)

