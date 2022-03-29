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

import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt
from IPython.display import display, HTML
import gzip
from fpdf import FPDF
from pandas.plotting import table
from geopy.geocoders import Nominatim
from subprocess import check_output, STDOUT

def sql_edit(configname, string):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    c.execute(string)
    conn.commit()
    conn.close()

def sql_fetch(string, configname):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    c.execute(string)
    data = c.fetchall()
    conn.close()
    return data


def insert_consensus_name(entryid, configname, consensus_name):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    entryid_statement = "entryid = '{}'".format(entryid)

    dbstring = "UPDATE isolatetable SET consensus_name = '{}' WHERE {}".format(consensus_name, entryid_statement)
    print (dbstring)
    c.execute(dbstring)

    conn.commit()
    conn.close()

def insert_metadata_table(entryid, entries, values, configname):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()

    dbstring = "INSERT INTO metadatatable(entryid, {}) VALUES('{}', {})".format(entries, entryid.replace("'", "''"), values)

    c.execute(dbstring)

    conn.commit()
    conn.close()

def update_reference_table(entryid, amrgenes, virulencegenes, plasmids, header_text, configname):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    amrgenes_statement = "amrgenes = '{}'".format(amrgenes)
    virulencegenes_statement = "virulencegenes = '{}'".format(virulencegenes)
    plasmids_statement = "plasmids = '{}'".format(plasmids)
    if amrgenes != None:
        dbstring = "UPDATE referencetable SET {} WHERE header_text = '{}'".format(amrgenes_statement, header_text)
        c.execute(dbstring)
    if virulencegenes != None:
        dbstring = "UPDATE referencetable SET {} WHERE header_text = '{}'".format(virulencegenes_statement, header_text)
        c.execute(dbstring)
    if plasmids != None:
        dbstring = "UPDATE referencetable SET {} WHERE header_text = '{}'".format(plasmids_statement, header_text)
        c.execute(dbstring)

    conn.commit()
    conn.close()

def insert_amr_table(entryid, samplename, analysistimestamp, amrgenes, phenotypes, specie, risklevel, warning, configname):

    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()


    dbstring = "INSERT INTO amrtable(entryid, samplename, analysistimestamp, amrgenes, phenotypes, specie, risklevel, warning) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')"\
        .format(entryid, samplename, analysistimestamp, amrgenes, phenotypes, specie, risklevel, warning)
    c.execute(dbstring)

    conn.commit()
    conn.close()

def init_status_table(entryid, status, type, current_stage, final_stage, result, configname):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()

    dbstring = "INSERT INTO statustable(entryid, status, type, current_stage, final_stage, result) VALUES('{}', '{}', '{}', '{}', '{}', '{}')".format(
        entryid, status, type, current_stage, final_stage, result)
    c.execute(dbstring)
    conn.commit()
    conn.close()

def update_status_table(entryid, status, type, current_stage, final_stage, result, configname):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    entryid_statement = "entryid = '{}'".format(entryid)
    status_statement = "status = '{}'".format(status)
    type_statement = "type = '{}'".format(type)
    current_stage_statement = "current_stage = '{}'".format(current_stage)
    final_stage_statement = "final_stage = '{}'".format(final_stage)
    result_statement = "result = '{}'".format(result)
    time_statement = "time_stamp = '{}'".format(str(datetime.datetime.now())[0:-7])

    dbstring = "UPDATE statustable SET {}, {}, {}, {}, {}, {} WHERE {}".format(status_statement, type_statement, current_stage_statement, final_stage_statement, result_statement, time_statement, entryid_statement)
    c.execute(dbstring)

    conn.commit()
    conn.close()

def init_isolate_table(entryid, header_text, samplename, plasmid_string, allresgenes, virulence_string, configname, referenceid):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    dbstring = "INSERT INTO isolatetable(entryid, header_text, samplename, analysistimestamp, plasmids, amrgenes, virulencegenes, referenceid) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
        entryid, header_text, samplename, str(datetime.datetime.now())[0:-7], plasmid_string.replace("'", "''"),
        allresgenes.replace(", ", ",").replace("'", "''"), virulence_string.replace("'", "''"), referenceid)

    c.execute(dbstring)
    conn.commit()
    conn.close()

def update_isolate_table(entryid, header_text, samplename, plasmid_string, allresgenes, virulence_string, configname):
    conn = sqlite3.connect(configname + "moss.db")
    c = conn.cursor()
    entryid_statement = "entryid = '{}'".format(entryid)
    header_text_statement = "header_text = '{}'".format(header_text)
    samplename_statement = "samplename = '{}'".format(samplename)
    plasmid_string_statement = "plasmids = '{}'".format(plasmid_string)
    allresgenes_statement = "amrgenes = '{}'".format(allresgenes)
    virulence_string_statement = "virulencegenes = '{}'".format(virulence_string)

    dbstring = "UPDATE isolatetable SET {}, {}, {}, {}, {} WHERE {}".format(header_text_statement, samplename_statement, plasmid_string_statement, allresgenes_statement, virulence_string_statement, entryid_statement)
    c.execute(dbstring)

    conn.commit()
    conn.close()