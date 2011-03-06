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

from ovc import *
from ovc.ovctypes import *
#from ovc.newrecord import *
from ovc.util import mfclassic_getsector, getbits, mfclassic_getoffset


if __name__ == '__main__':

	if len(sys.argv) < 2:
		sys.stderr.write('Usage: %s <ovc_dump> [<ovc_dump_2> [...]]\n'%sys.argv[0])
		sys.exit(1)

	for fn in sys.argv[1:]:
		inp = open(fn, 'rb')
		data = inp.read()
		inp.close()

		if len(data) == 4096:	# mifare classic 4k
			print "Dump file: ", fn
			# card details
			# TODO make the card an object in itself with fixed-position templates
			# note that these data areas are not yet fully understood
			cardid = getbits(data[0:4], 0, 4*8)
			cardtype = OvcCardType(getbits(data[0x10:0x36], 18*8+4, 19*8))
			validuntil = OvcDate(getbits(data[0x10:0x36], 11*8+6, 13*8+4))
			s = 'OV-Chipkaart id %d, %s, valid until %s'%(cardid, cardtype, validuntil)
			if cardtype==2:
				birthdate = OvcBcdDate(getbits(mfclassic_getsector(data, 22), 14*8, 18*8))
				s += ', birthdate %s'%birthdate
			print s

			# subscriptions
			# Print the idsubs value for this subscription before it.
			# XXX if the subscriptions don't start in the first slot, and a new
			# one is added there, the numbers change???
			print "Subscriptions:"
			log_entry = 0
			for sector in range(32, 35):
				sdata = mfclassic_getsector(data, sector)[:-0x10]
				offset,size = mfclassic_getoffset(sector)
				for chunk in range(0, len(sdata), 0x30):
					if ord(sdata[chunk]) == 0: continue
					sys.stdout.write(('#%x=%03x: ' % (log_entry, offset + chunk)))
					print OvcClassicTransaction(sdata[chunk:chunk+0x30])
					log_entry += 1
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
					if l >= start_log_2: l = OvcMostRecentCreditIndex.map[l - start_log_2 - 1]
					elif   l >= start_log_1: l = l - start_log_1
					sys.stdout.write(('#%x=%03x: ' % (l, offset + chunk)))
					#print OvcClassicTransaction(sdata[chunk:chunk+0x20])
					print OvcVariableTransaction(sdata[chunk:chunk+0x20])

			# Credit at F90 and FA0
			print
			print "Credit: (current and previous)"
			sdata = mfclassic_getsector(data, 39)[:-0x10]
			offset,size = mfclassic_getoffset(39)

			saldo1 = OvcSaldo(sdata[0x90:0x90+0x10])
			saldo2 = OvcSaldo(sdata[0xa0:0xa0+0x10])
			s1 = "f90: " + str(saldo1)
			s2 = "fa0: " + str(saldo2)
			# Kan ook 'transact-id' van hieronder zijn...
			if saldo1.get('id') < saldo2.get('id'):
			    print s2; print s1
			else:
			    print s1; print s2

			# indexes at FB0, FD0
			print
			print "Main index (current and previous):"

			index1 = OvcIndexFB0(sdata[0xb0:0xb0+0x20])
			index2 = OvcIndexFB0(sdata[0xd0:0xd0+0x20])
			s1 = "fb0: " + str(index1)
			s2 = "fd0: " + str(index2)

			swap_dupl = index1.get('transact-id') < index2.get('transact-id')
			if swap_dupl:
			    print s2; print s1
			else:
			    print s1; print s2

			# indexes at F50, F70
			print
			print "Check-in and outcheck-out indexes:"

			index1 = OvcIndexF50(sdata[0x50:0x50+0x20])
			index2 = OvcIndexF70(sdata[0x70:0x70+0x20])
			s1 = "f50: " + str(index1)
			s2 = "f70: " + str(index2)

			print s1
			print s2

			# indexes at F10, F30
			print
			print "Most recent subscription:  KLOPT NIET"
			index1 = OvcIndexF10(sdata[0x10:0x10+0x20])
			index2 = OvcIndexF10(sdata[0x30:0x30+0x20])
			s1 = "f10: " + str(index1)
			s2 = "f30: " + str(index2)

			if swap_dupl:
			    print s2; print s1
			else:
			    print s1; print s2
			
			# at F00: just zeros
			#print "f00: %x" % (getbits(sdata[0:0x10], 0, 16*8))


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

