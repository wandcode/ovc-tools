#!/usr/bin/env python

import os
import sys
import sqlite3

# name of database
dbname = 'stations.sqlite'
# sql file to create tables
createsql = 'create_tables.sql'
# default table for importing data files
dfl_table = 'stations_data'
machine_table = 'machines_data'
subscription_table = 'subscriptions_data'

prefix = os.path.dirname(os.path.realpath(__file__))
db = os.path.join(prefix, dbname)

def dbconnect(_db = None):
	'''open connection to database'''
	global db
	if not _db: _db = db
	con = sqlite3.connect(_db)
	return con

def tsv_each(filename):
	'''iterate over lines in tsv file'''
	f = open(filename, 'r')
	fields = None
	for line in f:
		if line == "": continue
		if line.startswith('#'): continue
		try: line = line[:line.index('#')]
		except ValueError: pass
		data = [x.strip() for x in line.decode('utf-8').split('\t')]
		if not fields:
			fields = data
		else:
			yield dict(zip(fields, data))
	f.close()

def readfile(filename):
	'''return contents of textfile'''
	f = open(filename, 'r')
	r = f.read()
	f.close()
	return r


if __name__ == '__main__':

	if os.path.exists(db):
		sys.stderr.write('Please remove database file first: %s\n'%db)
		sys.exit(1)

	con = dbconnect()
	cur = con.cursor()
	# performance improvements
	cur.executescript('''
		PRAGMA journal_mode = OFF;
		PRAGMA locking_mode = EXCLUSIVE;
		PRAGMA foreign_keys = ON;
	''')

	# create tables first
	print 'Creating tables'
	cur.executescript(readfile(os.path.join(prefix, createsql)))

	# then import all other sql files
	for filename in os.listdir(prefix):
		if not filename.endswith('.sql'): continue
		if filename == createsql: continue
		if (len(sys.argv) > 1):
                	if( sys.argv[1] == 'android' ):
				if filename[0:22] == "create_tables_machines": continue
				if filename[0:27] == "create_tables_subscriptions": continue
		else:
			if filename[0:21] == "create_tables_android": continue

		print 'Importing SQL: %s'%filename
		cur.executescript(readfile(os.path.join(prefix, filename)))

	# Defer foreign key constraints first.
#	cur.executescript('BEGIN;')

	# and import tab-separated files; first line are fields,
	# hash '#' at start of a line is a comment
	for filename in os.listdir(prefix):
		if not filename.endswith('.tsv'): continue
		if (len(sys.argv) > 1):
                        if( sys.argv[1] == 'android' ):
                        	if filename[0:7] == "machine": continue
				if filename[0:12] == "subscription": continue
		print 'Importing tab-separated data: %s'%filename
		if filename[0:7] == "machine":
		    table = machine_table
		elif filename[0:12] == "subscription":
		    table = subscription_table
		else:
		    table = dfl_table
		for fields in tsv_each(os.path.join(prefix, filename)):
			query = 'INSERT INTO %s (%s) VALUES (%s);'%(
					table,
					','.join(fields.keys()),
					','.join(['?'] * len(fields.values())),
				)
			try:
			    cur.execute(query, fields.values())
			except sqlite3.IntegrityError as ex:
			    print ex
			    print fields
		
	# Only now we have all data, the foreign key constraints can be checked
#	cur.executescript('COMMIT;')

	# compact database
	print 'Compacting database'
	cur.executescript('''
		VACUUM;
	''')

	con.close()
	print 'Done!'
