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
# (c)2011 by ocsr@unl
#
from ovc.OvcNewRecord import *

class OvcVariableRecord(OvcNewRecord):
    '''Interpret binary records with variable data fields. Needs to be subclassed.'''

    _fields = []
    _order = None

    def __init__(self, data, ovc):
        OvcNewRecord.__init__(self, data, ovc)

    def parse(self, **kwargs):
        identifier = self.getbits(0, 28)
	return self.parse2(identifier, 28, self._fields)

    def parse2(self, identifier, start, fields):
	start0 = start
	done = 0
        for field in fields:
            name, mask, width, fieldtype = field
            #print name, mask, width, fieldtype
            if (mask == None) or (identifier & mask):
                bits = self.getbits(start, width)
                #print name, start, width, bits
                start += width
                self.field[name] = fieldtype(bits, obj=self, width=width, ovc=self.ovc)
                self.desc[name] = field

		# Recursively process nested 'identifiers'
		if isinstance(self.field[name], OvcVariableSubRecord):
		    width = self.field[name].parse(start=start)
		    start += width

                if mask != None:
                    done = done | mask
        if done ^ identifier != 0:
            print "Unknown bits in identifier: %04x (%04x)" % (done ^ identifier, identifier)
	end = len(self.data) * 8
	if start < end:
	    width = end - start
	    self._rest = FixedWidthHex(self.getbits(start, width), obj=self, width=width)
	    if self._rest == 0:
		self._rest = None
	else:
	    self._rest = None
        # everything is ok, incorporate fields
        self.__dict__.update(self.field)
	return start - start0
    
    def __str__(self):
        res = ""
	if self._order != None:
	    for name in self._order:
		if name in self.field:
		    res += str(self.field[name]) + " "
		elif name[0] == ":":
		    res += name[1:]
	else:
	    for field in self._fields:
		name, start, width, fieldtype = field
		#print name, start, width, fieldtype
		if name in self.field:
		    res += str(self.field[name]) + " "
	if self._rest != None:
	    res += " Rest:" + str(self._rest)
        return res

class OvcVariableSubRecord(OvcVariableRecord):

    def __init__(self, value, obj, **kwargs):
        OvcVariableRecord.__init__(self, obj.data, ovc=obj.ovc)
	self.base_obj = obj
	self.identifier = value

    def parse(self, start, **kwargs):
	width = self.parse2(self.identifier, start, self._fields)
	self._rest = None
	self.propagate()
	return width

    def propagate(self):
        # incorporate fields into base object
        self.base_obj.__dict__.update(self.field)
	self.base_obj.field.update(self.field)

