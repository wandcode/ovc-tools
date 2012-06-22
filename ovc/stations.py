#
# OV-chipkaart decoder: station database access
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#        
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License at http://www.gnu.org/licenses/gpl.txt
# By using, editing and/or distributing this software you agree to
# the terms and conditions of this license.
#
# (c)2010 by Willem van Engen <dev-rfid@willem.engen.nl>
#

import os
import sys
import sqlite3


class OvcStation:
	'''single station'''

	# fields the are always present (regardless or database, albeit possibly None)
	_fields = ['company', 'ovcid', 'title', 'name', 'fullname', 'city', 'zone', 'lonlat']

	def __init__(self, d):
		self.__dict__.update(dict.fromkeys(self._fields))
		self.__dict__.update(d)
	
	def __str__(self):
		return self.title

class OvcMachine:
	'''single station'''

	# fields the are always present (regardless or database, albeit possibly None)
	_fields = ['company', 'machineid', 'title', 'ovcid', 'vehicleid']

	def __init__(self, d):
		self.__dict__.update(dict.fromkeys(self._fields))
		self.__dict__.update(d)
	
	def __str__(self):
		return str(self.company) + "." + str(self.machineid)

db = None
con = None
def init(_db=None):
	global db, con
	db = _db
	if not db: db = os.path.join(os.path.dirname(__file__), '..', 'stations', 'stations.sqlite')
	if not os.path.exists(db):
		sys.stderr.write('WARNING: No station database found, please run stations/createdb.py\n')
		return
	# for convenience also warn if any file in stations is newer than database file
	dbtime = os.path.getmtime(db)
	for filename in os.listdir(os.path.dirname(db)):
		if not filename.endswith('.tsv') or filename.endswith('.sql'): continue
		ftime = os.path.getmtime(os.path.join(os.path.dirname(db), filename))
		if ftime > dbtime:
			sys.stderr.write('WARNING: Station database older than its source files, ')
			sys.stderr.write('you may want to rerun stations/createdb.py\n')
	con = sqlite3.connect(db)

def get_station(company, number):
	'''return station object by number'''
	global con
	if not con: init()
	if not con: return None
	cur = con.cursor()
	cur.execute('SELECT * FROM stations WHERE company=? AND ovcid=?', (company, number))
	row = cur.fetchone()
	# If company is TLS (unknown, set badly) try NS instead
	if not row and company == 0:
	    company = 4
	    cur.execute('SELECT * FROM stations WHERE company=? AND ovcid=?', (company, number))
	    row = cur.fetchone()
	if not row:return None
	return OvcStation(dict(zip([x[0] for x in cur.description], row)))

def get_machine(company, number):
	'''return machine object by number'''
	global con
	if not con: init()
	if not con: return None
	cur = con.cursor()
	cur.execute('SELECT * FROM machines_data WHERE company=? AND machineid=?', (company, number))
	row = cur.fetchone()
	if not row: return None
	m = OvcMachine(dict(zip([x[0] for x in cur.description], row)))
	if m.ovcid != None:
	    return get_station(company, m.ovcid)
	if m.vehicleid == None:
	    m.title = "???"
	else:
	    m.title = "in vehicle %d" % m.vehicleid
	return m

def get_ovcids_by_machine(company, machid):
	'''return ovcids for a numbered machine'''
	global con
	if not con: init()
	if not con: return None
	cur = con.cursor()
	cur.execute('SELECT ovcid FROM machines_data WHERE company=? AND machineid=?', (company, machid))
	#rows = cur.fetchall()
	rows = [ x[0] for x in cur ]
	return rows

def get_vehicleids_by_machine(company, machid):
	'''return ovcids for a numbered machine'''
	global con
	if not con: init()
	if not con: return None
	cur = con.cursor()
	cur.execute('SELECT vehicleid FROM machines_data WHERE company=? AND machineid=?', (company, machid))
	rows = [ x[0] for x in cur ]
	return rows

def get_max_len(table='stations', field='title', company=None):
	'''return maximum length of station names'''
	global con
	if not con: init()
	if not con: return 0
	where=''
	if company is not None: where = 'WHERE company=%d'%company
	cur = con.cursor()
	cur.execute('SELECT MAX(LENGTH(%s)) FROM %s %s'%(field, table, where))
	return int(cur.fetchone()[0])

