#
# OV-chipkaart decoder: record interpretation
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
# (c)2011 by <ocsr@unl>
#

from util import getbits
from ovctypes import *
from OvcFixedRecord import *
from OvcVariableRecord import *

class OvcSector22(OvcNewRecord):
    def __init__(self, data, cardtype, ovc):
        OvcNewRecord.__init__(self, data, ovc)
	self.cardtype = cardtype

    def __str__(self):
	s = ""
	offset = 0
	const1 = self.getbits(offset, 6*8)
	offset += 6*8
	unknown1 = self.getbits(offset, 8*8)
	offset += 8*8
	if self.cardtype == 2:
	    birthdate = OvcBcdDate(self.getbits(14*8, 4*8))
	    offset += 5*8
	    s += 'birthdate %s, '%birthdate
	const2 = self.getbits(offset, 3*8)
	offset += 3*8
	autocharge = AutoCharge(self.data, self.ovc, offset=offset)
	s += str(autocharge)
	s += "(%x %x %x)" % (const1, unknown1, const2)
	return s

class AutoCharge(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('activated',        0,      3,     FixedWidthHex),
            ('limit',            3,     16,     OvcAmount),
            ('charge',          19,     16,     OvcAmount),
            ('unk1',            35,     16,     FixedWidthHex),
        ]

    def __init__(self, data, ovc, offset):
        OvcFixedRecord.__init__(self, data, ovc, offset=offset)

    def __str__(self):
	s = ""
	if self.activated == 4:
	    s += "no autocharge, "
	elif self.activated == 5:
	    s += "autocharge, "
	else:
	    s += "autocharge #%x, " % self.activated
	s += "limit:" + str(self.limit)
	s += ", charge:" + str(self.charge)
	s += "(%x)" % (self.unk1)
	return s
