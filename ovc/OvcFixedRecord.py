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
# (c)2011 by ....
#

#import re
from util import getbits
from ovctypes import *
from ovc.OvcNewRecord import *

class OvcFixedRecord(OvcNewRecord):
    '''Interpret binary records with fixed data fields. Needs to be subclassed.'''

    _fields = []
    _order = None

    def __init__(self, data, ovc, offset=0, **kwargs):
        OvcNewRecord.__init__(self, data, ovc, offset=offset)
        self.parse()

    def parse(self):
	self.parse2(self._fields)

    def parse2(self, fields):
        for field in fields:
            name, start, width, fieldtype = field
	    if fieldtype != None:
		bits = self.getbits(self.offset + start, width)
		#print name, start, width, fieldtype
		self.field[name] = fieldtype(bits, obj=self,width=width,ovc=self.ovc)
		self.desc[name] = field
        # everything is ok, incorporate fields
        self.__dict__.update(self.field)
    
    def __str__(self):
        res = ""
	if self._order != None:
	    for name in self._order:
		if name in self.field:
		    res += str(self.field[name]) + " "
	else:
	    for field in self._fields:
		name, start, width, fieldtype = field
		if fieldtype == None:
		    res += name
		else:
		    res += str(self.field[name]) + " "
        return res

    def mkarray(self, membertype, name, bitwidth):
        arr = []
        name, start, width, fieldtype = self.desc[name]
        for off in xrange(0, width - bitwidth + 1, bitwidth):
            one = self.getbits(start + off, bitwidth)
            arr.append(membertype(one, obj=self, ovc=self.ovc, width=bitwidth))
        return arr
