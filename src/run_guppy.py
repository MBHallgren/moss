#!/usr/bin/env python3

# Copyright (c) 2019, Malte Hallgren Technical University of Denmark
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

# create the parser for the "surveillance" command


parser = argparse.ArgumentParser(description='.')
parser.add_argument('-i', action="store", type=str, dest='input', default="", help='input')
parser.add_argument('-name', action="store", type=str, dest='name', default="", help='name')
parser.add_argument('-bk', action="store", type=str, dest='bk', default="", help='bk')
parser.add_argument('-chunks', action="store", type=str, dest='chunks', default="", help='chunks')
parser.add_argument('-c', action="store", type=str, dest='model', default="", help='model')
args = parser.parse_args()

def main(args):
    check_input_name(args)
    os.system("mkdir /opt/moss_data/fastq/{}".format(args.name))
    base_call(args)

def check_input_name(args):
    files = os.listdir("/opt/moss_data/fast5/")
    if args.name in files:
        sys.exit("This experiment name has already been used. Please choose another one.")

def base_call(args):
        cmd = "/opt/ont/guppy/bin/guppy_basecaller -i {}  -s /opt/moss_data/fastq/{}/ --device \"cuda:0\" --compress_fastq --trim_barcodes --barcode_kits {}".format(
            args.input, args.name, args.bk)
        if "sup" in args.model:
            cmd += " -c {} --chunks_per_runner 256".format(args.model)
        else:
            cmd += " -c {}".format(args.model)
        print (cmd)
        os.system(cmd)
        dir_list = os.listdir("/opt/moss_data/fastq/{}/pass/".format(args.name))
        print (dir_list)
        for item in dir_list:
            cmd = "cat /opt/moss_data/fastq/{}/pass/{}/* > /opt/moss_data/fastq/{}/{}_{}.fastq.gz".format(args.name, item, args.name, args.name, item)
            os.system(cmd)
        os.system("rm /opt/moss_data/fastq/{}/guppy_basecaller_log*".format(args.name))
        os.system("rm /opt/moss_data/fastq/{}/*unclassified*".format(args.name))
if __name__ == '__main__':
    main(args)