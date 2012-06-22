#!/usr/bin/env python

# Helper script to import machine IDs when only the names of the
# locations are given.
# For those machine IDs that are not yet in the database,
# it prints the ovcid. It has to guess if it needs the ticket-machine
# ovcid or the check-in-ovcid, for stations that have different
# values for these.
# THAT IS why it is better to keep the association of the numbers
# directly, so you can directly find out which ovcid a particular
# machine uses.
# Note that it always prints "4" for the company id.

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
	return True

def lookup_ovcid(name):
	'''return station number by name'''
	global con
	cur = con.cursor()
	cur.execute('SELECT ovcid FROM stations WHERE title=?', (name,))
	rows = cur.fetchall()
	if not rows: return None
	# rows = [(875,), (876,)]
	return ",".join(str(x[0]) for x in rows)

def lookup_ticket_ovcid(name):
	ovcid = lookup_ovcid("**" + name)
	if ovcid != None: return ovcid
	ovcid = lookup_ovcid("*" + name)
	if ovcid != None: return ovcid
	return lookup_ovcid(name)

def lookup_other_ovcid(name):
	return lookup_ovcid(name)

def lookup_any_ovcid(machid, name):
    if seems_ticket_machine(machid):
	return lookup_ticket_ovcid(name)
    else:
	return lookup_other_ovcid(name)

def seems_ticket_machine(machineid):
    # NS
    machineid = int(machineid)
    if 460000 <= machineid <= 461999:
	return True
    # Arriva
    if 262000 <= machineid <= 262999:
	return True
    return False

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
		print line
		continue
	    print "#", line
	    if " - " in line:
		(num, name) = line.split(" - ")
		#print "num =", num
		#print "name =", name
		if not lookup_machineid(num):
		    ovcid = lookup_any_ovcid(num, name)
		    sys.stdout.write("4\t%s\t%s\t# %s\n" % (num, ovcid, name))
	f.close()
	cur.close()
	con.close()
