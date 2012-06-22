#!/usr/bin/env python
#
# OV-chipkaart decoder: main program
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
import sys
import getopt

from ovc import *
from ovc.ovctypes import *
from ovc.util import mfclassic_getsector, getbits, mfclassic_getoffset
import ovc.config

class ovc4k(object):
    def __init__(self, data):
	self.data = data

	# Derived fields
	self.subscr = {}
	self.subscr_aux = {}

	self.saldo_curr = None
	self.saldo_curr_prefix = None
	self.saldo_prev = None
	self.saldo_next_prefix = None

	self.FB0_curr = None
	self.FB0_curr_prefix = None
	self.FB0_prev = None
	self.FB0_next_prefix = None

	self.F50_curr = None
	self.F50_prev = None

	self.F10_curr = None
	self.F10_curr_prefix = None
	self.F10_prev = None
	self.F10_next_prefix = None

    def parse(self):
	data = self.data	# convenience abbreviation

	# Sector 39, 0xF00, for various indexes
	sdata = mfclassic_getsector(data, 39)[:-0x10]
	offset,size = mfclassic_getoffset(39)

	# at F00: just zeros
	#print "f00: %x" % (getbits(sdata[0:0x10], 0, 16*8))

	# indexes at FB0, FD0
	index1 = OvcIndexFB0(sdata[0xb0:0xb0+0x20], ovc=self)
	index2 = OvcIndexFB0(sdata[0xd0:0xd0+0x20], ovc=self)
	s1 = "fb0:"
	s2 = "fd0:"

	if index1.get('transact-id') < index2.get('transact-id'):
	    self.FB0_curr = index2
	    self.FB0_curr_prefix = s2
	    self.FB0_prev = index1
	    self.FB0_prev_prefix = s1
	else:
	    self.FB0_curr = index1
	    self.FB0_curr_prefix = s1
	    self.FB0_prev = index2
	    self.FB0_prev_prefix = s2

	latest_credit = self.FB0_curr.latest_credit
	latest_travel = self.FB0_curr.latest_travel
	latest_subscr = self.FB0_curr.latest_subscr

	# Credit at F90 and FA0
	locs = [ 0x90, 0xa0 ]
	loc_curr = locs[latest_credit]
	loc_prev = locs[1 - latest_credit]
	self.saldo_curr = OvcSaldo(sdata[loc_curr:loc_curr+0x10], ovc=self)
	self.saldo_prev = OvcSaldo(sdata[loc_prev:loc_prev+0x10], ovc=self)
	self.saldo_curr_prefix = "%3x:" % (0xf00 + loc_curr)
	self.saldo_prev_prefix = "%3x:" % (0xf00 + loc_prev)

	# indexes at F10, F30, 0x20 long
	locs = [ 0x10, 0x30 ]
	loc_curr = locs[latest_subscr]
	loc_prev = locs[1 - latest_subscr]
	self.F10_curr = OvcIndexF10(sdata[loc_curr:loc_curr+0x20], ovc=self)
	self.F10_prev = OvcIndexF10(sdata[loc_prev:loc_prev+0x20], ovc=self)
	self.F10_curr_prefix = "%3x:" % (0xf00 + loc_curr)
	self.F10_prev_prefix = "%3x:" % (0xf00 + loc_prev)

	# indexes at F50, F70;
	# something to do with travel (check in/out) transactions
	locs = [ 0x50, 0x70 ]
	loc_curr = locs[latest_travel]
	loc_prev = locs[1 - latest_travel]
	self.F50_curr = OvcIndexF50(sdata[loc_curr:loc_curr+0x20], ovc=self)
	self.F50_prev = OvcIndexF50(sdata[loc_prev:loc_prev+0x20], ovc=self)
	self.F50_curr_prefix = "%3x:" % (0xf00 + loc_curr)
	self.F50_prev_prefix = "%3x:" % (0xf00 + loc_prev)

	self.F50_curr.setIndexes(self.FB0_curr)
	self.F50_prev.setIndexes(self.FB0_prev)

    def printit(self):
	data = self.data

	# card details
	# note that these data areas are not yet fully understood
	cardid = getbits(data[0:4], 0, 4*8)
	cardtype = OvcCardType(getbits(data[0x10:0x36], 18*8+4, 19*8))
	validuntil = OvcDate(getbits(data[0x10:0x36], 11*8+6, 13*8+4))
	s = 'OV-Chipkaart id %d, %s, valid until %s'%(cardid, cardtype, validuntil)
	#if cardtype==2:
	#	birthdate = OvcBcdDate(getbits(mfclassic_getsector(data, 22), 14*8, 18*8))
	#	s += ', birthdate %s'%birthdate
	print s

	for sector in range(22, 24):
		sdata = mfclassic_getsector(data, sector)[:-0x10]
		offset,size = mfclassic_getoffset(sector)
		sector22 = OvcSector22(sdata, ovc=self, cardtype=cardtype)
		print ("%3x:" % offset), sector22

	print ""

	# subscriptions
	# Print the slot number value for this subscription before it and the idsubs after it.
	print "Subscriptions:"
	log_entry = 0
	for sector in range(32, 35):
		sdata = mfclassic_getsector(data, sector)[:-0x10]
		offset,size = mfclassic_getoffset(sector)
		for chunk in range(0, len(sdata), 0x30):
			l = log_entry
			log_entry += 1
			if ord(sdata[chunk]) == 0: continue
			addr = offset + chunk
			sys.stdout.write(('#%x=%03x: ' % (l, addr)))
			#Oldest method:
			#print OvcClassicTransaction(sdata[chunk:chunk+0x30])
			#sys.stdout.write('      : ')
			#Method #2:
			#print OvcSubscriptionRecord.make(sdata[chunk:chunk+0x30], ovc=self)
			#sys.stdout.write('      : ')
			#Method #3:
			s = OvcVariableSubscription(sdata[chunk:chunk+0x30], ovc=self)
			print s
			aux_addr = OvcSubscriptionAux.addr(l)
			aux_sdata = data[aux_addr:aux_addr+0x10]
			sys.stdout.write(('   %03x: ' % (aux_addr)))
			s_aux = OvcSubscriptionAux(aux_sdata, ovc=self)
			print s_aux, OvcSubscriptionId(self.find_subscr_id(l))

			self.subscr[l] = s
			self.subscr_aux[l] = s_aux
	# transactions
	print "Transaction logs: (history, checkin/out, credit)"
	# Entries  0-10: for User, chronologic, may be erased?
	# Entries 11-23: for Conductor, not chronologic, only one check-in
	# Entries 24-27: add Credit transactions
	start_log_0 = 0
	start_log_1 = 11
	start_log_2 = 24
	log_entry = 0
	for sector in range(35, 39):
		sdata = mfclassic_getsector(data, sector)[:-0x10]
		offset,size = mfclassic_getoffset(sector)
		for chunk in range(0, len(sdata), 0x20):
			if (chunk + 0x20) > len(sdata): continue	# last few bytes, not big enough
			l = log_entry
			log_entry += 1
			if l == start_log_1 or l == start_log_2: print "--"
			if ord(sdata[chunk]) == 0: continue
			if   l >= start_log_2: l = OvcMostRecentCreditIndex.map[l - start_log_2 - 1]
			elif l >= start_log_1: l = l - start_log_1
			sys.stdout.write(('#%x=%03x: ' % (l, offset + chunk)))
			#print OvcClassicTransaction(sdata[chunk:chunk+0x20])
			print OvcVariableTransaction(sdata[chunk:chunk+0x20], ovc=self)

	print
	print "Credit: (current and previous)"
	print self.saldo_curr_prefix, str(self.saldo_curr)
	print self.saldo_prev_prefix, str(self.saldo_prev)
	if not self.saldo_prev.id <= self.saldo_curr.id:
	    print "Order bit 250 in 0xFB0/FD0 contradicted by id order"
	print
	print "Main index (current and previous):"
	print self.FB0_curr_prefix, str(self.FB0_curr)
	print self.FB0_prev_prefix, str(self.FB0_prev)
	print
	print "Check-in and check-out indexes (current and previous):"
	print self.F50_curr_prefix, str(self.F50_curr)
	print self.F50_prev_prefix, str(self.F50_prev)
	print
	print "Most recent subscription (current and previous):"
	print self.F10_curr_prefix, str(self.F10_curr)
	print self.F10_prev_prefix, str(self.F10_prev)
	if not self.F10_prev.size <= self.F10_curr.size:
	    # Maybe this will also occur if nearly all slots are taken
	    # and they are being re-used
	    print "Order bit 248 in 0xFB0/FD0 contradicted by subscription order (list getting full?)"

    def find_subscr_id(self, slotnr):
	# Find the subscription ID corresponding to the subscription slot number
	# This is the inverse of the index FB0.subscr_id_to_slot_nr.
	arr = self.FB0_curr.subscr_id_to_slot_nr
	for i in xrange(0, len(arr)):
	    if arr[i] == slotnr:
		return i + 1
	return -1

if __name__ == '__main__':

	if len(sys.argv) < 2:
		sys.stderr.write('Usage: %s <ovc_dump> [<ovc_dump_2> [...]]\n'%sys.argv[0])
		sys.exit(1)

	args = sys.argv[1:]
	optlist, args = getopt.getopt(args, '?', ['mismatch', 'stations', 'vehicles'])

	for o, v in optlist:
	    if o == "--mismatch":
		config.check_mismatch = True
	    elif o == "--stations":
		config.print_new_station = True
	    elif o == "--vehicles":
		config.print_new_vehicle = True
		print "print_new_vehicles"

	for fn in args:
		inp = open(fn, 'rb')
		data = inp.read()
		inp.close()

		if len(data) == 4096:	# mifare classic 4k
			print "Dump file: ", fn
			ovc = ovc4k(data)
			ovc.parse()
			ovc.printit()

		elif len(data) == 64:	# mifare ultralight GVB
			# TODO card id, otp, etc.
			for chunk in range(0x10, len(data)-0x10, 0x10):
				# skip empty slots
				if data[chunk:chunk+2] == '\xff\xff': continue
				# print data
				t = OvcULTransaction(data[chunk:chunk+0x10])
				t.company = OvcCompany(2)
				print t

		else:
			sys.stderr.write('%s: expected 4096 or 64 bytes of ov-chipkaart dump file\n'%fn)
			sys.exit(2)

