#
# OV-chipkaart decoder: mifare dump utilities
#
# (may move to separate package when substantial enough)
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

def getbits(data, start, end):
	'''Return number at bit positions of bytestring data (msb first)'''
	val = 0L
	#verbose = (start == 4 and end == 6)
	for byte in range(start/8, (end+7)/8):
		bits = 8	# to chop off excess bits on the right
		if byte*8 > end-8: bits = end - byte*8
		#if verbose: print "byte =", byte, "bits =", bits
		mask = 0xff	# to chop off excess bits on the left
		if byte == start/8: mask = (1<<(8-start%8))-1
		#if verbose: print "mask = %02x" % mask
		val = (val << bits) + ((ord(data[byte]) & mask)>>(8-bits))
		#if verbose: print "data[byte] = %02x val = %02x" % (ord(data[byte]), val)
	return val

def mfclassic_getoffset(sector):
	'''Calculate sector offset and size for mifare classic'''
	if sector < 32:
		length = 0x40
		addr = sector*length
	else:
		length = 0x100
		addr = 0x800 + (sector-32)*length
	return addr, length

def mfclassic_getsector(data, sector):
	'''Retrieve sector from mifare classic dump'''
	addr, length = mfclassic_getoffset(sector)
	return data[addr:addr+length]

def bcd2int(x):
	return int('%x'%x)

