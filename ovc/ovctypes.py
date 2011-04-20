#
# OV-chipkaart decoder: field types
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

import datetime
import stations
from util import bcd2int
import config
import sys

def _rfill(s, l):
	'''Fill string right with spaces to make as long as longest value in list/dict'''
	return s + ' '*(_maxlength(l)-len(s))

def _maxlength(l):
	'''Return maximum length of strings in (nested) list or dict'''
	if isinstance(l, dict): l = l.values()
	if isinstance(l, list): return max([_maxlength(x) for x in l])
	return len(l)


class OvcDate(datetime.date):
	'''date with ovc-integer constructor (days)'''
	# TODO subclassing this built-in type doesn't work fully :(
	def __new__(cls, x, **kwargs):
		days = x
		d = datetime.date.__new__(cls, 1997, 1, 1)
		d += datetime.timedelta(days)
		return d
	def __str__(self):
		return self.strftime('%d-%m-%Y')


#class OvcTime(datetime.time):
#	'''time with ovc-integer constructor (minutes)'''
#	# TODO subclassing this built-in type doesn't work fully :(
#	def __new__(cls, x, **kwargs):
#		minutes = x
#		d = datetime.time.__new__(cls, 0)
#		d = d + datetime.timedelta(0, minutes * 60)
#		return d
#	def __str__(self):
#		return self.strftime('%H:%m')

class OvcTime(object):
	'''time with ovc-integer constructor (minutes)'''
	# TODO subclassing the built-in type datetime.time doesn't work fully :(
	def __init__(self, x, **kwargs):
		minutes = x
		if minutes < 0:
		    self.present = False
		    self.hours = self.minutes = 0
		else:
		    self.present = True
		    self.hours = minutes / 60
		    self.minutes = minutes % 60
	def __str__(self):
		if self.present:
		    return "%02d:%02d" % (self.hours, self.minutes)
		else:
		    return "--:--"

class OvcDatetime(datetime.datetime):
	'''datetime with ovc-integer constructor (combined days and minutes)'''
	# TODO subclassing this built-in type doesn't work fully :(
	def __new__(cls, x, **kwargs):
		d = datetime.datetime.__new__(cls, 1997, 1, 1)
		d += datetime.timedelta(x>>11, (x&((1<<11)-1))*60)
		return d
	def __str__(self):
		return self.strftime('%d-%m-%Y %H:%m')

class OvcBcdDate(datetime.date):
	'''date with ovc-BCD constructor'''
	def __new__(cls, x, **kwargs):
		day   = bcd2int((x>> 0)&0xff)
		month = bcd2int((x>> 8)&0xff)
		year  = bcd2int((x>>16)&0xffff)
		if not year: return None
		return datetime.date.__new__(cls, year, month, day)

class OvcCardType(int):
	_strs = { 0: 'anonymous', 2: 'personal'}
	def __new__(cls, x, **kwargs):
		return int.__new__(cls, x)
	def __str__(self):
		try: return self._strs[self]
		except KeyError: return 'cardtype %d'%self

class OvcAction(int):
	_strs = {
		  0: 'purchase',  1: 'check-in', 2: 'check-out',
		  4: 'opla/con', 12: 'controle',
		  6: 'transfer',
		}
	def __new__(cls, x, **kwargs):
		return int.__new__(cls, x)
	def __str__(self):
		try: return _rfill(self._strs[self], self._strs)
		except KeyError: return _rfill('Action %d'%self, self._strs)

class OvcCompany(int):
	# most companies can be figured out using
	# https://www.ov-chipkaart.nl/webwinkel/aanvragen/aanvragen_pkaart/kaartaanvragen/?ovbedrijf=<number>
	# pending: Breng (Novio), GVU, Hermes, Qbuzz
	# company 25 is used for credit machines at Albert Heijn, Primera and in Hermes busses
	# company 26 has been seen as well
	_strs = {
		 0: 'TLS',         1: 'Connexxion',  2: 'GVB',        3: 'HTM',
		 4: 'NS',          5: 'RET',                          7: 'Veolia',
		 8: 'Arriva',      9: 'Syntus',
		12: 'DUO',
		25: 'AH/Primera',
	     15001: 'AH/PrimerA',	# include extra bits on the left of the field
	}
	def __new__(cls, x, **kwargs):
		return int.__new__(cls, x)
	def __str__(self):
		try: return _rfill(self._strs[self], self._strs)
		except KeyError: return _rfill('company %d'%self, self._strs)

class OvcSubscription(int):
	_strs = {
		 1: {	# Connexxion
		        0x0692: 'Daluren Oost-Nederland (1682)',
		        0x069c: 'Daluren Oost-Nederland (1692)',	# both have been seen
		},
		 2: {	# GVB (Amsterdam)
 			0x0bbd: 'Supplement fiets',
		}, 
		 4: {	# NS
			0x0005: 'OV-jaarkaart',
			0x0007: 'OV-bijkaart 1e klas',
			0x0011: 'NS business card',
			0x0019: '2-jaar Voordeelurenabonnement',
			0x00af: 'Studenten week vrij 2009',
			0x00b0: 'Studenten weekend vrij 2009',
			0x00b1: 'Studenten korting week 2009',
			0x00b2: 'Studenten korting weekend 2009',
			0x00c9: 'Reizen op saldo (1e klas)',
			0x00ca: 'Reizen op saldo (2e klas)',
			0x00ce: 'Voordeelurenabonnement',
			0x00e5: '1e klas (1 dag)',
			0x00e6: '2e klas (1 dag)',
			0x00e7: '1e klas (1 dag) (korting)',
		},
		 7: {   # Veolia
		        0x0626: 'DALU Dalkorting',
	        },
		 8: {	# Arriva
			0x059a:	'Voordeeluren',	# uit 035BD45C.dump
		},
		12: {
			0x09c6: "Student, weekend-vrij",
			0x09c7: "Student, week-discount",
			0x09c9: "Student, week-vrij",
			0x09ca: "Student, weekend-discount",
		}
	}
	def __new__(cls, x, obj, **kwargs):
		i = int.__new__(cls, x)
		i._obj = obj
		return i
	def __str__(self):
		try:
		    return _rfill(self._strs[self._obj.company][self], self._strs)
		except KeyError:
		    # The field got changed with 8 more bits at the right. This caused all
		    # numbers to change. Try to chop off some bits to compensate.
		    # This is a temporary hack.
		    try:
			return _rfill(self._strs[self._obj.company][self >> 8], self._strs)
		    except KeyError:
			return _rfill('subscription %d'%self, self._strs)

_ostwidth = 0
class OvcStation(int):
	def __new__(cls, x, obj, **kwargs):
		i = int.__new__(cls, x)
		i._obj = obj
		return i
	def __str__(self):
		# compute maximum length of station name and cache it
		global _ostwidth
		if not _ostwidth: _ostwidth = stations.get_max_len('stations', 'title')
		# get station name and pad string
		s = stations.get_station(self._obj.company, self)
		if not s or not s.title:
			s = '(station %5d)'%self
		else:
			s = s.title
		return s + ' '*(_ostwidth-len(s))

_omwidth = 0
_hdr = None

class OvcMachineId(long):
	def __new__(cls, x, obj, width=0, **kwargs):
		i = long.__new__(cls, x)
		i._fieldwidth = width
		i._obj = obj
		return i
	def __str__(self):
		# return "M:"+('%d'%long(self)).zfill(self._fieldwidth)
		# compute maximum length of machine name and cache it
		global _omwidth
		if not _omwidth: _omwidth = 10
		if not _omwidth: _omwidth = stations.get_max_len(table='stations', field='title')
		# get machine name
		s = stations.get_machine(self._obj.company, self)
		if not s or not s.title:
			s = ''
			if config.print_new_station:
			    if 'station' in self._obj.__dict__ and \
				    not 'vehicle' in self._obj.__dict__:
				global _hdr
				if _hdr != "s":
				    sys.stderr.write("# company\tmachineid\tovcid\n")
				    _hdr = "s"
				sys.stderr.write("%d\t%d\t%d\n" % (self._obj.company, int(self), self._obj.station))
			if config.print_new_vehicle:
			    if 'vehicle' in self._obj.__dict__:
				global _hdr
				if _hdr != "v":
				    sys.stderr.write("# company\tmachineid\tvehicleid\n")
				    _hdr = "v"
				sys.stderr.write("%d\t%d\t%d\n" % (self._obj.company, int(self), self._obj.vehicle))
		else:
			s = "(" + s.title + ")"
		s = s + ' '*(_omwidth-len(s))
		return "M:"+('%7d'%long(self))+s

#class OvcTransactionId(int):
#	def __new__(cls, x,  **kwargs):
#		return int.__new__(cls, x)
#	def __str__(self):
#		return '#%03d'%self
#
#class OvcSaldoTransactionId(int):
#	def __new__(cls, x,  **kwargs):
#		return int.__new__(cls, x)
#	def __str__(self):
#		return '$%03d'%self

# The Transaction ID can also be a Credit Transacion ID, if it is in a
# Credit Transaction. We want to distinguish them because it counts
# independently of normal Transaction IDs.
# I use a horrible hack here to convert one to the other.
class OvcTransactionId(int):
	def __new__(cls, x, obj, **kwargs):
#		try:
#		    # For identifiers 08_10_55_0 and not for 28_00_55_6
#		    # or 29_00_55_4.  Basically this tests for the
#		    # absence of 'idsubs' but at the time this code
#		    # runs it has not been parsed yet.
#		    if not (ord(obj.data[0]) & 0x20):
#			return OvcSaldoTransactionId(x)
#		except AttributeError:
#		    pass
		return int.__new__(cls, x)
	def __str__(self):
		return '#%03d'%self

class OvcSaldoTransactionId(OvcTransactionId):
	def __new__(cls, x,  **kwargs):
		return int.__new__(cls, x)
	def __str__(self):
		return '$%03d'%self

class OvcSubscriptionId(int):
	def __new__(cls, x,  **kwargs):
		return int.__new__(cls, x)
	def __str__(self):
		return 'S:%02d'%self

class OvcAmount(float):
	'''amount in euro; prints '-' when zero'''
	def __new__(cls, x, **kwargs):
		return float.__new__(cls, x/100.0)
	def __str__(self):
		if self < 1e-6: return '      -  '
		return 'EUR%6.2f'%self

class OvcAmountSigned(float):
	'''amount in euro; 16 bit signed number'''
	def __new__(cls, x, **kwargs):
 		x = x - (1<<15)
		return float.__new__(cls, x/100.0)
	def __str__(self):
		return 'EUR%6.2f'%self

class OvcVehicleId(long):
	def __new__(cls, x, width=0, **kwargs):
		i = long.__new__(cls, x)
		i._fieldwidth = ( 3 * width + 9) / 10
		return i
	def __str__(self):
		return "V:"+('%d'%long(self)).zfill(self._fieldwidth)

class FixedWidthDec(long):
	def __new__(cls, x, width=0, **kwargs):
		i = long.__new__(cls, x)
		i._fieldwidth = ( 3 * width + 9) / 10
		return i
	def __str__(self):
		return ('%d'%long(self)).zfill(self._fieldwidth)

class FixedWidthHex(long):
	def __new__(cls, x, width=0, **kwargs):
		i = long.__new__(cls, x)
		i._fieldwidth = (width + 3) / 4
		return i
	def __str__(self):
		return '0x'+('%x'%self).zfill(self._fieldwidth)

class FixedWidthBin(long):
	def __new__(cls, x, width=0, **kwargs):
		i = long.__new__(cls, x)
		i._fieldwidth = width
		return i
	def __str__(self):
		s = ""
		for b in xrange(self._fieldwidth - 1, -1, -1):
		    if self & (1L << b):
			s += "1"
		    else:
			s += "0"
		return s

def tobin(string):
    s = ""
    for ch in string:
	bits = ord(ch)
	s0 = ""
	for b in xrange(7, -1, -1):
	    if bits & (1 << b):
		s0 += "1"
	    else:
		s0 += "0"
	s += s0 + " "
    return s

class HistoryTransactionAddr(int):
	def __new__(cls, x, width=0, **kwargs):
		i = int.__new__(cls, x)
		i._fieldwidth = width
	        #addr = i < 7 ? (0xB00 + i * 0x20) : (0xC00 + (i - 7) * 0x20)
		if x < 7: addr = 0xB00 + x * 0x20
		else:     addr = 0xC00 + (x - 7) * 0x20
		i._addr = addr
		return i
	def __str__(self):
		return ('#%x=0x%x'%(self,self._addr)).zfill(self._fieldwidth)

#class HistoryTransactionAddr(object):
#	def __init__(self, x, width=0, **kwargs):
#		self.i = x
#		self._fieldwidth = width
#	        #addr = i < 7 ? (0xB00 + i * 0x20) : (0xC00 + (i - 7) * 0x20)
#		if x < 7: addr = 0xB00 + x * 0x20
#		else:     addr = 0xC00 + (x - 7) * 0x20
#		self._addr = addr
#		#return self
#	def __str__(self):
#		return ('#%x=0x%x'%(self.i,self._addr)).zfill(self._fieldwidth)

class CheckInOutTransactionAddr(int):
	def __new__(cls, x, width=0, **kwargs):
		i = int.__new__(cls, x)
		i._fieldwidth = width
		if   x <  3: addr = 0xC80 +  x       * 0x20
		elif x < 10: addr = 0xD00 + (x -  3) * 0x20
		else:        addr = 0xE00 + (x - 10) * 0x20
		i._addr = addr
		return i
	def __str__(self):
		return ('#%x=0x%x'%(self,self._addr)).zfill(self._fieldwidth)

# Look up through the index of check in/out transactions in
# FB0/FD0.
class CheckInOutTransactionAddrIndex(int):
	def __new__(cls, x, ovc, obj, width=0, **kwargs):
		i = int.__new__(cls, x)
		i._fieldwidth = width
		i._ovc = ovc
		i._base_obj = obj.base_obj
		i._checks = []
		i._derefd = None
		return i

	def setIndexes(self, typeFB0):
		self._checks = typeFB0.checks

	def __str__(self):
		if self._derefd == None:
		    checks = self._checks
		    if self >= 0 and self < len(checks):
			self._derefd = checks[self-1]
		    else:
			self._derefd = "?"
		return ('%x->'%self) + str(self._derefd)

class OvcMostRecentCreditIndex(int):
	# For some reasons, the entries in this 3-long list are numbered 1, 6 and 8.
	map = [ 1, 6, 8 ]
	rev = { 1: 0, 6: 1, 8: 2 }
	def __new__(cls, x, width=0, **kwargs):
		i = int.__new__(cls, x)
		i._fieldwidth = width
		try:
		    addr = 0xe80 + OvcMostRecentCreditIndex.rev[x] * 0x20
		except KeyError:
		    addr = 0
		i._addr = addr
		return i
	def __str__(self):
	    return ('Credit_Tr:#%x=0x%x'%(self,self._addr)).zfill(self._fieldwidth)

class OvcSubscriptionLogIndex(int):
	def __new__(cls, x, width=0, **kwargs):
		i = int.__new__(cls, x)
		i._fieldwidth = width
		if x > 0:
		    addr = (x - 1) * 0x30
		    if x >  5: addr += 0x10	# skip sector trailer
		    if x > 10: addr += 0x10	# skip sector trailer
		    i._addr = 0x800 + addr
		else:
		    i._addr = 0
		return i
	def __str__(self):
	    return ('Subscr:#%x=0x%x'%(self,self._addr)).zfill(self._fieldwidth)

