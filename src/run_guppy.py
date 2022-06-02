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
    files = os.listdir(args.input)
    barcode_list = list()
    for item in files:
        if "barcode".upper() in item.upper():
            barcode_list.append(item)
    print (len(barcode_list))
    if len(barcode_list) == 0:
        print (cmd)
        cmd = "/opt/moss/ont-guppy/bin/./guppy_basecaller -i {}/*  -s /opt/moss_data/fastq/{}/ --device \"cuda:0\" --compress_fastq --trim_barcodes -c {}".format(
            args.input, args.name, args.model)
        os.system(cmd)
    else:
        for item in barcode_list:
            print (cmd)
            cmd = "/opt/moss/ont-guppy/bin/./guppy_basecaller -i {}/{}/*  -s /opt/moss_data/fastq/{}/{} --device \"cuda:0\" --compress_fastq --trim_barcodes -c {}".format(args.input, item, args.name, item, args.model)
            os.system(cmd)
    #for item in barcode_list:
    #    os.system("cat /opt/moss_data/fastq/{}/{}/pass/{}/*.fastq.gz > /opt/moss_data/fastq/{}/{}_{}.fastq.gz".format(args.name, item, args.name, args.name, item))
    #os.system("rm -rf /opt/moss_data/fastq/{}/pass/".format(args.name))
if __name__ == '__main__':
    main(args)