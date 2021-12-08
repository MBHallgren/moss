# Copyright (c) 2019, Malte Bjørn Hallgren Technical University of Denmark
# All rights reserved.
#

#Import Libraries
import sys
import os
import argparse
import operator
import time
import geocoder
import gc
import numpy as np
import array
import subprocess
import threading
from optparse import OptionParser
from operator import itemgetter
import re
import json
import sqlite3
import json
import datetime
import hashlib
import gzip
import posix_ipc
import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt
from IPython.display import display, HTML
import gzip
from fpdf import FPDF
from pandas.plotting import table
from geopy.geocoders import Nominatim
from subprocess import check_output, STDOUT

def init_status_table(entryid, status, type, level_current, level_max, result, db_dir):
    conn = sqlite3.connect(db_dir + "moss.db")
    c = conn.cursor()

    dbstring = "INSERT INTO statustable(entryid, status, type, level_current, level_max, result) VALUES('{}', '{}', '{}', '{}', '{}', '{}')".format(
        entryid, status, type, level_current, level_max, result)
    c.execute(dbstring)
    conn.commit()
    conn.close()

def update_status_table(entryid, status, type, level_current, level_max, result, db_dir):
    conn = sqlite3.connect(db_dir + "moss.db")
    c = conn.cursor()
    entryid_statement = "entryid = '{}'".format(entryid)
    status_statement = "status = '{}'".format(status)
    type_statement = "type = '{}'".format(type)
    level_current_statement = "level_current = '{}'".format(level_current)
    level_max_statement = "level_max = '{}'".format(level_max)
    result_statement = "result = '{}'".format(result)

    dbstring = "UPDATE statustable SET {}, {}, {}, {}, {} WHERE {}".format(status_statement, type_statement, level_current_statement, level_max_statement, result_statement, entryid_statement)
    print (dbstring)
    c.execute(dbstring)

    conn.commit()
    conn.close()

def init_isolate_table(entryid, header_text, samplename, plasmid_string, allresgenes, virulence_string, db_dir):
    conn = sqlite3.connect(db_dir + "moss.db")
    c = conn.cursor()
    dbstring = "INSERT INTO isolatetable(entryid, header_text, samplename, analysistimestamp, plasmids, amrgenes, virulencegenes) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
        entryid, header_text, samplename, str(datetime.datetime.now())[0:-7], plasmid_string.replace("'", "''"),
        allresgenes.replace(", ", ",").replace("'", "''"), virulence_string.replace("'", "''"))

    c.execute(dbstring)
    conn.commit()
    conn.close()

def update_isolate_table(entryid, header_text, samplename, plasmid_string, allresgenes, virulence_string, db_dir):
    conn = sqlite3.connect(db_dir + "moss.db")
    c = conn.cursor()
    entryid_statement = "entryid = '{}'".format(entryid)
    header_text_statement = "header_text = '{}'".format(header_text)
    samplename_statement = "samplename = '{}'".format(samplename)
    plasmid_string_statement = "plasmid_string = '{}'".format(plasmid_string)
    allresgenes_statement = "allresgenes = '{}'".format(allresgenes)
    virulence_string_statement = "virulence_string = '{}'".format(virulence_string)

    dbstring = "UPDATE isolatetable SET {}, {}, {}, {}, {} WHERE {}".format(header_text_statement, samplename_statement, plasmid_string_statement, allresgenes_statement, virulence_string_statement, entryid_statement)
    print (dbstring)
    c.execute(dbstring)

    conn.commit()
    conn.close()