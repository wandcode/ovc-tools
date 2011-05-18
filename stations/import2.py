#!/usr/bin/env python

# Helper script to import machine IDs when also the numbers
# locations are given.
# For those machine IDs that are not yet in the database,
# it prints a line to add to the textual database.
# For the ones present, it checks if it is consistent.

import os
import sys
import sqlite3

# name of database
dbname = 'stations.sqlite'
# default table for importing data files
station_table = 'stations_data'
machine_table = 'machines_data'

prefix = os.path.dirname(__file__)
db = os.path.join(prefix, dbname)

def dbconnect(_db = None):
	'''open connection to database'''
	global db
	if not _db: _db = db
	con = sqlite3.connect(_db)
	return con

def lookup_machineid(machineid):
	'''return machine info by number'''
	global con
	cur = con.cursor()
	cur.execute('SELECT * FROM machines_data WHERE machineid=?', (machineid,))
	row = cur.fetchone()
	if not row: return False
	return row

def lookup_ovcid(name):
	'''return station number by name'''
	global con
	cur = con.cursor()
	cur.execute('SELECT ovcid FROM stations WHERE title=?', (name,))
	rows = cur.fetchall()
	if not rows: return None
	# rows = [(875,), (876,)]
	return ",".join(str(x[0]) for x in rows)

company_to_id = {
	"Connexxion": 2,
	"GVB": 2,
	"HTM": 3,
	"NS": 4,
	"RET": 5,
	"Veolia": 7,
	"Arriva": 8,
	"Syntus": 9,
}

if __name__ == '__main__':

	con = dbconnect()
	cur = con.cursor()
	# performance improvements
	cur.executescript('''
		PRAGMA journal_mode = OFF;
		PRAGMA locking_mode = EXCLUSIVE;
	''')
    
	# f = open("newids", "r")
	f = sys.stdin
	for line in f:
	    # chop newline
	    line = line[0:-1]
	    if line.startswith("#"):
		#print line
		continue
	    #print "#", line
	    try:
		(machid, ovcid, name, company, kind, contributor, remark) = line.split("\t")
		ovcid = int(ovcid)
	    except:
		continue
	    #print "num =", num
	    #print "name =", name
	    company_id = company_to_id[company]

	    found = lookup_machineid(machid)

	    printit = False
	    if found == False:
		printit = True
	    else:
		(old_company_id, dummy, old_ovcid, dummy) = found
		if old_company_id != company_id:
		    printit = True
		    print "# company mismatch: %d" % old_company_id
		if old_ovcid != ovcid:
		    printit = True
		    print "# ovcid mismatch: %d" % old_ovcid
		if printit:
		    sys.stdout.write("# ")

	    if printit:
		c = "" if contributor == "Anonymous" else contributor
		sys.stdout.write("%s\t%s\t%s\t# %s %s %s\n" % (company_id, machid, ovcid, name, c, remark))
		    
	f.close()
	cur.close()
	con.close()
