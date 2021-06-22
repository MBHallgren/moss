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
import datetime
import threading
import posix_ipc

#Use Argparse to correctly open the inputfiles

# create the parser for the "surveillance" command


parser = argparse.ArgumentParser(description='.')
parser.add_argument('-info', type=int, help='surveillance info')
parser.add_argument('-i_illumina', action="store", type=str, dest='i_illumina', nargs="+", default="", help='The path to the directory containing ONLY the input illumina files. Should be used when analyzing >5 read-files at a time.')
parser.add_argument('-i_nanopore', action="store", type=str, dest='i_nanopore', default="", help='The path to the directory containing ONLY the input nanopore files. Should be used when analyzing >5 read-files at a time.')
#parser.add_argument('-i_assemblies', action="store", type=str, dest='i_assemblies', default="", help='The path to the directory containing the assembly files')
parser.add_argument("-masking_scheme", type=str, action="store", dest="masking_scheme", default="", help="Give a fasta file containing a motof that you wish to mask in the aligned concensus files.")
parser.add_argument("-prune_distance", type=int, action="store", dest="prune_distance", default=5, help="X lenght that SNPs can be located between each other. Default is 10. If two SNPs are located within X lenght of eachother, everything between them as well as X lenght on each side of the SNPs will not be used in the alignments to calculate the distance matrix.")
parser.add_argument("-bc", action="store", type=float, default = 0.7, dest="bc", help="Base calling parameter for nanopore KMA mapping. Default is 0.7")
parser.add_argument("-db_dir", action="store", type=str, default = "", dest="db_dir", help="Comeplete path to the database directory generated by running moss.py. Default name is dbdir.")
parser.add_argument("-thread", action="store", default = 1, dest="multi_threading", help="Set this parameter to x-number of threads that you would like to use during KMA-mapping.")
parser.add_argument("-o", action="store", dest="output_name", help="Name that you would like the output directory to be called.")
parser.add_argument('-version', action='version', version='moss 1.0.0', help = "Current version of PathogenRealTimeTyper.")
parser.add_argument("-exepath", action="store", dest="exepath", default = "", help="Complete path to the moss repo that you cloned, in which your kma and ccphylo folder at located.")
args = parser.parse_args()

jobid = random.randint(1,100000000)





if args.db_dir != "":
    db_dir = moss.correctPathCheck(args.db_dir)
else:
    sys.exit("no moss database path was given.")
if args.exepath != "":
    exepath = moss.correctPathCheck(args.exepath)
else:
    sys.exit("No exepath was given.")


def SurveillancePipeline(i_illumina, i_nanopore, masking_scheme, prune_distance, bc,
                         db_dir, multi_threading, output_name, exepath):


    #Check if an assembly is currently running and status on other semaphores
    moss.semaphoreInitCheck() #Wait here is writing is taking place in reference DB.
    print ("semaphore check complete")



    start_time = datetime.datetime.now()



    inputType, total_filenames, assemblyType = moss.mossCheckInputFiles(i_illumina, i_nanopore)


    reference = ""
    kma_path = exepath + "kma/kma"
    ccphylo_path = exepath + "ccphylo/ccphylo"
    referencedb = db_dir + "REFDB.ATG"
    isolatedb = db_dir + "moss.db"
    datafiles = db_dir + "datafiles"

    referenceSyncFile = db_dir + "syncFiles/referenceSync.json"
    isolateSyncFile = db_dir + "syncFiles/isolateSync.json"

    if inputType == "nanopore":
        inputname = i_nanopore.split("/")[-1]
        entryid = moss.md5(i_nanopore)
    elif inputType == "pe_illumina":
        inputname = i_illumina[0].split("/")[-1]
        illumina_name1 = i_illumina[0].split("/")[-1]
        illumina_name2 = i_illumina[1].split("/")[-1]
        entryid = moss.md5(i_illumina[0])

    elif inputType == "se_illumina":
        inputname = i_illumina[0].split("/")[-1]
        entryid = moss.md5(i_illumina[0])

    moss.uniqueNameCheck(db_dir, inputType, total_filenames)

    moss.processQueuedAnalyses(db_dir, output_name, inputname, entryid)

    if output_name[0] == "/":
        target_dir = db_dir + "analysis/" + output_name.split("/")[-1] + "/"
    else:
        target_dir = db_dir + "analysis/" + output_name + "/"
    cmd = "mkdir " + target_dir
    os.system(cmd)
    kma_database_path = referencedb

    logfilename = target_dir + "logfile_" + output_name
    logfile = open(logfilename, 'w')

    cmd = "mkdir " + target_dir + "datafiles"
    os.system(cmd)

    # Print messages
    startTime = time.time()
    print("# Running MinION-Typer 1.0.0 with following input conditions:", file=logfile)
    print ("-input: {}".format(total_filenames), file = logfile)
    print ("-input: {}".format(total_filenames))
    moss.logfileConditionsResearch(logfile, masking_scheme, prune_distance, bc, kma_database_path, multi_threading, reference, output_name)
    print("# -prune_distance: " + str(prune_distance), file=logfile)
    if bc != 0:
        print("# -bc: " + str(bc), file=logfile)
    if kma_database_path != "":
        print("# -db: " + kma_database_path, file=logfile)
    if multi_threading != 1:
        print("# -thread: " + str(multi_threading), file=logfile)
    if reference != "":
        print("# -ref: " + reference, file=logfile)
    print("loading input")

    moss.runResFinder(exepath, total_filenames, target_dir)
    moss.runPlasmidFinder(exepath, total_filenames, target_dir)
    moss.runVirulenceFinder(exepath, total_filenames, target_dir)
    best_template_score, template_found, templatename = moss.findTemplateSurveillance(total_filenames, target_dir, kma_database_path, logfile, kma_path)

    best_template = moss.findTemplateNumber(db_dir, templatename)

    print ("Best template number: {}".format(best_template), file = logfile)
    print ("Best template: {}".format(templatename), file = logfile)

    # best_template, best_template_score, template_found, templatename = moss.findTemplateSurveillance(total_filenames, target_dir, kma_database_path, logfile, kma_path)

    #Template mapping works 16/8

    print ("Input file analysed was: {}".format(total_filenames))

    print("Score of the best template was: " + str(best_template_score))

    if template_found == False: #NO TEMPLATE FOUND #Being assembly
        print ("assebly stop", file = logfile)

        if assemblyType == "illumina":
            moss.inputAssemblyFunction(assemblyType, inputType, target_dir, i_illumina, illumina_name1, illumina_name2, "", jobid, inputname, kma_path, kma_database_path, entryid, referenceSyncFile, isolatedb, db_dir)
        elif assemblyType == "nanopore":
            moss.inputAssemblyFunction(assemblyType, inputType, target_dir, i_illumina, "", "", i_nanopore, jobid, inputname, kma_path, kma_database_path, entryid, referenceSyncFile, isolatedb, db_dir)

        end_time = datetime.datetime.now()
        run_time = end_time - start_time
        print("Run time: {}".format(run_time))
        print("Run time: {}".format(run_time), file=logfile)

        moss.endRunningAnalyses(db_dir, output_name, inputname, entryid)

        logfile.close()
        sys.exit("No template was found, so input was added to references.")

    #If reference found:

    #Check that no assembly started during template finding
    semaphore = posix_ipc.Semaphore("/IndexRefDB", posix_ipc.O_CREAT, initial_value=1)
    assembly_semaphore_value = semaphore.value
    if assembly_semaphore_value == 0: #Extremely rare, so not a big deal and this potentially only could lead to a slide missplacement which can then be fixed the the redistribution algorithm
        print ("An assembly started during template finding. Consider running the redistribution algorithm of {} if you think the two current inputs could be closely related. This is unlikely but possible!".format(templatename))
        try:
            semaphore.acquire(timeout=18000)  # Wait maxium of 5 hours. Illumina assemblies can take a lot of time, but should not exceed 5h.
            semaphore.release()  # No assembly running, clear to go

        except posix_ipc.BusyError as error:
            semaphore.unlink()
            print("IndexRefDB semaphore is jammed")
            print("Unlinking IndexRefDB semaphore")

    if " " in templatename:
        templateaccesion = templatename.split(" ")[0]
    else:
        templateaccesion = templatename

    if inputType == "pe_illumina":
        moss.illuminaMappingPE(i_illumina, best_template, target_dir, kma_database_path, logfile, multi_threading, kma_path, templateaccesion)
    elif inputType == "se_illumina":
        moss.illuminaMappingForward(i_illumina, best_template, target_dir, kma_database_path, logfile, multi_threading, kma_path, templateaccesion)
    if inputType == "nanopore":
        moss.nanoporeMapping(i_nanopore, best_template, target_dir, kma_database_path, logfile, multi_threading, bc, kma_path, templateaccesion)
    #Make function to look up and write template_kma scores to logfile



    #Make comp for both illumina and nanopore!

    #SQL TIME
    conn = sqlite3.connect(isolatedb)
    c = conn.cursor()

    c.execute("SELECT * FROM referencetable WHERE headerid = '{}'".format(templatename))
    refdata = c.fetchall()
    conn.close()

    refname = refdata[0][2]


    #cmd = "rm {}template_kma_results*".format(target_dir)
    #os.system(cmd)

    cmd = "cp {}{}_{}_consensus.fsa {}datafiles/isolatefiles/{}/{}_{}_consensus.fsa".format(target_dir, inputname, templateaccesion, db_dir, templateaccesion, inputname, templateaccesion)
    os.system(cmd)

    ######## KØR FREM PÅ CCPHYLO COMMANDO
    #CCind her. single fil som skal appendes til eksisterende matrix med samme, gemte conditions.
    if len(moss.loadFiles("{}datafiles/isolatefiles/{}/".format(db_dir, refname))) > 1:
        print ("CCPHYLO")
        cmd = "{} dist -i {}datafiles/isolatefiles/{}/* -r \"{}\" -mc 0.01 -nm 0 -o {}distance_matrix_{}".format(ccphylo_path, db_dir, refname, templatename, target_dir, refname)
        print (cmd, file = logfile)
        if prune_distance != 0 :
            cmd += " -pr {}".format(prune_distance)
        os.system(cmd)

        # Check if acceptable snp distance
        distance = moss.ThreshholdDistanceCheck("{}distance_matrix_{}".format(target_dir, refname), refname, "{}_{}_consensus.fsa".format(inputname, templateaccesion))
        print (distance, file = logfile)
        if distance > 300: #SNP distance
            print("Distance to best template was over 300 basepairs, so input will be defined as reference")
            if assemblyType == "illumina":
                moss.inputAssemblyFunction(assemblyType, inputType, target_dir, i_illumina, illumina_name1, illumina_name2, "", jobid, inputname, kma_path, kma_database_path, entryid, referenceSyncFile, isolatedb, db_dir)
            elif assemblyType == "nanopore":
                moss.inputAssemblyFunction(assemblyType, inputType, target_dir, i_illumina, "", "", i_nanopore, jobid, inputname, kma_path, kma_database_path, entryid, referenceSyncFile, isolatedb, db_dir)

            cmd = "rm {}datafiles/isolatefiles/{}/{}_{}_consensus.fsa".format(db_dir, templateaccesion, inputname, templateaccesion, referenceSyncFile, isolatedb, db_dir)
            os.system(cmd)
            """
            semaphore = posix_ipc.Semaphore("/ReferenceJSON", posix_ipc.O_CREAT, initial_value=1)
            try:
                semaphore.acquire(timeout=3600)
            except posix_ipc.BusyError as error:
                semaphore.unlink()
                print("Could not connect to ReferenceJSON semaphore")
                print("Unlinking semaphore and reacquiring it")
                print("Could not connect to ReferenceJSON semaphore", file = logfile)
                print("Unlinking semaphore and reacquiring it", file = logfile)
                semaphore = posix_ipc.Semaphore("/ReferenceJSON", posix_ipc.O_CREAT, initial_value=1)
                semaphore.acquire(timeout=3600)
            """
    
            with open(referenceSyncFile) as json_file:
                referenceobj = json.load(json_file)
            json_file.close()
            referenceobj['timestamp'] = str(time.time()) #NEEDS FIX
            with open(referenceSyncFile, 'w') as f_out:
                json.dump(referenceobj, f_out)
            f_out.close()
            #semaphore.release()


            # Reassemble
            end_time = datetime.datetime.now()
            run_time = end_time - start_time
            print("Run time: {}".format(run_time))

            moss.endRunningAnalyses(db_dir, output_name, inputname, entryid)
            #Claim semaphore
            sys.exit("Found template, but input fra over 300bp away, and input was assembled and defied as new reference")

        #Succesfull in finding reference, thus is semaphore not claimed continue:


        cmd = "cp {}distance_matrix_{} {}/datafiles/distancematrices/{}/distance_matrix_{}".format(target_dir, refname, db_dir, refname, refname)
        os.system(cmd)
        cmd = "{} tree -i {}/datafiles/distancematrices/{}/distance_matrix_{} -o {}/datafiles/distancematrices/{}/tree.newick".format(ccphylo_path, db_dir, refname, refname, db_dir, refname)
        os.system(cmd)
        moss.generateFigtree("{}/datafiles/distancematrices/{}/tree.newick".format(db_dir, refname), jobid)

        if refdata[0][3] == None:
            isolateid = entryid
        else:
            isolateid = refdata[0][3] + ", " + entryid

        conn = sqlite3.connect(isolatedb)
        c = conn.cursor()

        dbstring = "UPDATE referencetable SET isolateid = '{}' WHERE headerid = '{}'".format(isolateid, templatename)
        c.execute(dbstring)

        dbstring = "INSERT INTO isolatetable(entryid, isolatename) VALUES('{}', '{}')".format(entryid, inputname)
        c.execute(dbstring)

        conn.commit()
        conn.close()

        semaphore = posix_ipc.Semaphore("/IsolateJSON", posix_ipc.O_CREAT, initial_value=1)
        try:
            semaphore.acquire(timeout=3600)
        except posix_ipc.BusyError as error:
            semaphore.unlink()
            print ("Could not connect to IsolateJSON semaphore")
            print ("Unlinking semaphore and reacquiring it")
            semaphore = posix_ipc.Semaphore("/IsolateJSON", posix_ipc.O_CREAT, initial_value=1)
            semaphore.acquire(timeout=3600)

        with open(isolateSyncFile) as json_file:
            IsolateJSON = json.load(json_file)
        json_file.close()
        IsolateJSON[inputname] = {'entryid': entryid, 'headerid': templatename, 'refname': refname}
        with open(isolateSyncFile, 'w') as f_out:
            json.dump(IsolateJSON, f_out)
        f_out.close()
        semaphore.release()

        end_time = datetime.datetime.now()
        run_time = end_time - start_time
        print("Run time: {}".format(run_time))
        print("Run time: {}".format(run_time), file=logfile)

        moss.endRunningAnalyses(db_dir, output_name, inputname, entryid)

        cmd = "python3 {}src/outbreak_finder.py -db_dir {}".format(exepath, db_dir)
        os.system(cmd)

        moss.complileReport("testday", target_dir, entryid)

        logfile.close()



    else:
        print ("No isolate files were found the isolate folder, so no distance matrix was estimated. Check your logfile for system failure, something went wrong")





def main():
    if len(args.i_illumina) == 2:
        inputCheck = "Succes"
    elif len(args.i_illumina) == 1:
        inputCheck = args.i_illumina[0] + args.i_nanopore
    else:
        inputCheck = args.i_nanopore
    if inputCheck == "":
        sys.exit("No input was given.")
    SurveillancePipeline(args.i_illumina, args.i_nanopore, args.masking_scheme, args.prune_distance, args.bc, db_dir, args.multi_threading, args.output_name, args.exepath)


if __name__== "__main__":
  main()
