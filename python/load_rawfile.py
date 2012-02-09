#!/usr/bin/python2.6
####################
# load_rawfile.py #
VERSION = 0.1
####################

#Imported modules
import sys
from os import system, popen
from MySQLdb import *
import os.path
import datetime
import glob
from subprocess import *

# import pipeline utilities
import epta_pipeline_utils as epu

import config

def Help():
    print "\nLoad raw files to database"
    print "Version: %.2f"%(VERSION)+"\n"
    print ("'%s' accepts only raw files. Wildcard allowed.\n")% sys.argv[0]
    sys.exit(0)

def parse_psrfits_header(file):
    tmpbuf = ["psredit", "-q"]
    tmpbuf.append("-c")
    hdritems = ["nbin", "nchan", "npol", "nsubint", "type", "site", \
		"name", "type", "coord", "freq", "bw", "dm", "rm", \
		"dmc", "rmc", "polc", "scale", "state", "length", \
		"rcvr:name", "rcvr:basis", "be:name"]
    tmpbuf.append(",".join(hdritems))
    tmpbuf.append(file)
    
    hdrparams, errstr = epu.execute(" ".join(tmpbuf))
    #hdrparams = Popen(tmpbuf, stdout=PIPE, stderr=PIPE).communicate()
    return hdrparams
    

def get_userid(DBcursor, DBconn):
    uname=os.getlogin();
    QUERY = "SELECT user_id FROM users WHERE user_name = '%s'" % uname
    DBcursor.execute(QUERY)
    result = DBcursor.fetchall()
    if len(result) == 0:
        sys.stderr.write("user not found\n")
        return -1
    else:
        return result[0][0]

def get_pulsarid(DBcursor, DBconn, psrname):
    # added an extra '%' sign to pass a wildcard to mysql - so 1937+21 and B1937+21 are identified properly
    QUERY = "SELECT pulsar_id FROM pulsars WHERE pulsar_name like '%%%s'" % psrname
    DBcursor.execute(QUERY)
    result = DBcursor.fetchall()
    if len(result) == 0:
        sys.stderr.write("pulsar not found\n")
        return -1
    else:
        return result[0][0]
    

def get_obssystemid(DBcursor, DBconn, frontend, backend):
    QUERY = "SELECT obssystem_id FROM obssystems WHERE frontend = '%s' AND backend = '%s'" % (frontend, backend)
    DBcursor.execute(QUERY)
    result = DBcursor.fetchall()
    if len(result) == 0:
        sys.stderr.write(("Frontend/backend combination (%s/%s) " \
                            "not found in obssystems table\n") % \
                            (frontend, backend))
        return -1
    else:
        return result[0][0]
                                        
def populate_rawfiles_table(fname, DBcursor, DBconn, verbose=0):
    psr=''
    frontend=''
    backend=''
    # md5sum helper function in epu
    md5 = epu.Get_md5sum(fname);
    filepath, filename = os.path.split(os.path.abspath(fname))
    
    # Does this file exist already?
    QUERY = "SELECT rawfile_id FROM rawfiles WHERE md5sum = '%s'" % md5
    DBcursor.execute(QUERY)
    result = DBcursor.fetchall()
    if len(result) != 0:
        sys.stderr.write ("Rawfile in database already\n")
        return
    else:     
        # check if the file is indeed in psrfits format
        # Parse the psredit output
        if config.verbosity:
            print "Importing header information for %s \n" % fname
        param_names = parse_psrfits_header(fname)
        if "BAD PSRFITS FILE" in param_names:
            sys.stderr.write("Bad PSRFITS file. Trying running psredit manually on file\n")
            return -1
        # psredit reports sub:rows instead of nsub. Also change revr/be identifiers
        tmplist = param_names.replace("nsubint","nsub").replace("rcvr:","rcvr_").\
                  replace("be:","be_").replace("type","datatype").split()

        # find pulsar/backend and frontend
        for item in tmplist:
            tmpitem=item.split("=")
            if tmpitem[0] == "name":
                psr = tmpitem[1]
            elif tmpitem[0] == "be_name":
                backend = tmpitem[1]
            elif tmpitem[0] == "rcvr_name":
                frontend = tmpitem[1]

        pulsar_id = get_pulsarid(DBcursor, DBconn, psr)
        obssystem_id = get_obssystemid(DBcursor, DBconn, frontend, backend)
        user_id = get_userid(DBcursor, DBconn)
        add_time = epu.Make_Tstamp()

        if pulsar_id == -1 or obssystem_id == -1 or user_id == -1:
            sys.stderr.write("psr: %s frontend: %s backend: %s\n"%(psr, frontend, backend))
            sys.stderr.write("Not enough information\n")
            return -1

        # insert basic data, to get a rawfile_id
        QUERY = ( "INSERT INTO rawfiles SET md5sum = '%s', filename = '%s', filepath = '%s', \
        user_id = '%s', add_time ='%s', pulsar_id = '%s', obssystem_id = '%s'") \
        %(md5, filename, filepath, user_id, add_time, pulsar_id, obssystem_id)

        DBcursor.execute(QUERY)
        QUERY = "SELECT LAST_INSERT_ID()"
        DBcursor.execute(QUERY)
        rawfile_id = DBcursor.fetchall()[0][0]
        # from the result extracted from psrfits header, construct a query
        aa = [];
        for item in tmplist:
            # check if second field is a digit, if not it need to be a string for mysql
            if item.split("=")[1].replace(".","0").isdigit() == False:
                aa.append(item.split("=")[0] + "='" + item.split("=")[1] + "'")
            else:
                aa.append(item)
        # once the list is made compatible, ie, surround string with single-quotes, simply join
        QUERY = "UPDATE rawfiles SET " + ", ".join(aa) + " WHERE rawfile_id='%s'"%rawfile_id
        DBcursor.execute(QUERY)
        
    return rawfile_id

def create_diagnostics(rawfile_ids,DBcursor,DBconn):
    for rawfile_id in rawfile_ids:
        query = "select filepath,filename from rawfiles where datatype='intermediate' and rawfile_id='%i'"%rawfile_id
        DBcursor.execute(query)
        result = DBcursor.fetchall()

        if not len(result):
            print "No values found"
            pass
        else:
            result = result[0]

            file = os.path.join(result[0],result[1])
            filepath, filename = os.path.split(file)

            file_ext = filename.split(".")[-1]
            if file_ext == "fT":
                command = "pav -dG %s -g %s.png/png"%(file,file)
            elif file_ext == "Ft":
                command = "pav -Y %s -g %s.png/png"%(file,file)
            elif file_ext == "FT":
                command = "pav -S %s -g %s.png/png"%(file,file)
            elif file_ext == "FTp":
                command = "pav -DFTp %s -g%s.png/png"%(file,file)
            epu.execute(command)

def run_loader(file, DBcursor, DBconn):

    # Fill rawfile table
    if config.verbosity:
        print "Started %s at %s" % (populate_rawfiles_table.__name__, \
                                        epu.Give_UTC_now())
    rawfile_id = populate_rawfiles_table(file, DBcursor, DBconn, 1)

    if rawfile_id == -1:
        sys.stderr.write("Error loading file. %s returned %d\n"%(populate_rawfiles_table.__name__, rawfile_id))
    else:
        if config.verbosity:
            print "Finished %s at %s" % (populate_rawfiles_table.__name__,\
                                            epu.Give_UTC_now())
        print "File successfully loaded - rawfile_id: %s\n" % rawfile_id

    # fill-in parfiles table? This is to keep track of the
    # ephermeris used to fold the data.
    # New entry in parfiles is tables is needed to distinguish these parfiles.

def main():
    # Collect input files
    infiles = set(args.infiles)
    for glob_expr in args.glob_exprs:
        infiles.update(glob.glob(glob_expr))
    infiles = list(infiles)

    if not infiles:
        sys.stderr.write("You didn't provide any files load. " \
                         "You should consider including some next time...\n")
        sys.exit(1)
    # Create DB connection instance
    DBcursor, DBconn = epu.DBconnect()
    try:
        # Enter information in rawfiles table
        # create diagnostic plots and metrics.
        # Also fill-in raw_diagnostics and raw_diagnostic_plots tables
        for file in infiles:
            try:
                epu.Verify_file_path(file)
                run_loader(file, DBcursor, DBconn);
                #create_diagnostics(rawfile_id,DBcursor,DBconn)
            except errors.FileExistenceError:
                sys.stderr.write("File (%s) not found. Skipping..." % file)
    finally:
        # Close DB connection
        DBconn.close()


if __name__=='__main__':
    parser = epu.DefaultArguments(description="Archive raw files, " \
                                        "and load their info into the database.")
    parser.add_argument("infiles", nargs='*', action='store', \
                        help="Files with headers to correct.")
    parser.add_argument("-g", "--glob-files", action="append", \
                        dest='glob_exprs', default=[], \
                        help="Glob expression identifying files with " \
                             "headers to correct. Be sure to correctly " \
                             "quote the expression.")
    main()

