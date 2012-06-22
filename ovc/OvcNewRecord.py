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

import re
from util import getbits
from ovctypes import *

class OvcNewRecord(object):
    '''Interpret binary records. Needs to be subclassed.'''

    def __init__(self, data, ovc, offset=0, **kwargs):
        self.data = data
	self.ovc = ovc
        self.field = {}
        self.desc = {}
	self.offset = offset

    def get(self, name):
        return self.field[name]

    def getdata(self):
        return self.data

    def getbits(self, start, length):
        # return number at bit positions of data (0 is beginning)
        return getbits(self.data, start, start+length)
