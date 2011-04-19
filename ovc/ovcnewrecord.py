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
		self.field[name] = fieldtype(bits, obj=self,width=width)
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

def find_missing(array, lwb, upb):
    for i in xrange(lwb, upb + 1):
	found = False
	for j in array:
	    if i == j:
		found = True
		break;
	if not found:
	    return i
    return -1
   
class OvcIndexFB0(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('transact-id',     10,     16,     OvcTransactionId),
            ('unk1',             0,     10,     FixedWidthHex),
            ('unk2',            26,      6,     FixedWidthHex),
            ('ptr0_6_array_1', 4*8,    7*4,     FixedWidthHex),	# index 1
            ('ptr0_b_array_1', 7*8+4, 12*4,     FixedWidthHex), # index 2
	    ('Sbscr:',             0,    0,     None),
            ('subscr_ptrs',   13*8+4, 12*4,     FixedWidthHex), # index 3
	    ('Hist:',              0,    0,     None),
            ('history_ptrs',  19*8+4, 10*4,     FixedWidthHex), # index 4
           #('ptr0_b_array-3',24*8+4, 12*4,     FixedWidthHex),
	    ('Check:',             0,    0,     None),
            ('check_ptrs',    24*8+4, 12*4,     FixedWidthHex), # index 5
            ('recent_credit', 30*8+4,    4,     OvcMostRecentCreditIndex),
            ('latest_subscr',    248,    1,     FixedWidthHex),
            ('latest_travel',    249,    1,     FixedWidthHex),
            ('latest_credit',    250,    1,     FixedWidthHex),
            ('unk3',          31*8+3,    5,     FixedWidthHex),
        ]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)
        self.history = self.mkarray(HistoryTransactionAddr, 'history_ptrs', 4)
	self.next_history  = find_missing(self.history, 0x0, 0xa)
        self.checks  = self.mkarray(CheckInOutTransactionAddr, 'check_ptrs', 4)
	self.next_check  = find_missing(self.checks, 0x0, 0xc)
        self.checksmyst  = self.mkarray(CheckInOutTransactionAddr, 'ptr0_b_array_1', 4)
	self.next_checkmyst  = find_missing(self.checksmyst, 0x0, 0xc)
	# subscr_ptrs is an ordinary array mapping from subscription index
	# (OvcSubscriptionId) to subscription slot number; first entry is for
	# OvcSubscriptionId = 1.
	self.subscr_id_to_slot_nr = self.mkarray(FixedWidthDec, 'subscr_ptrs', 4)

    def __str__(self):
        res = "[index_FB0_] "
        res += OvcFixedRecord.__str__(self)
        #res += "\n     History (most recent first): " + str(map(str, self.history))
	res += "\n     next in logs               :           %x                                        %x                  %x" % (self.next_checkmyst, self.next_history, self.next_check)
        #res += "\n     Checks                     : " + str(map(str, self.checks))
	#res += "\n     next in checkin/out log    : %x" % self.next_check
	#res += "\n     next in mystery log        : %x" % self.next_checkmyst
        return res

class OvcIndexF50sub(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('company',         0,      8,     OvcCompany),	# 18 bits
            ('teller',          8,      4,     FixedWidthDec), #
            ('zeroes',         12,      6,     FixedWidthDec), #
        ]

    def __init__(self, data, ovc, **kwargs):
	# Data is an 18-bit integer, turn it into a string.
	# This is a hack, nested fixed records should be handled better.
	string = chr((data >> 10) & 0xFF) + \
	         chr((data >>  2) & 0xFF) + \
		 chr((data & 0x03) << 6)
        OvcFixedRecord.__init__(self, string, ovc)

    def __str__(self):
        res = ""
        res += OvcFixedRecord.__str__(self)
        return res

class OvcIndexF50(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('teller1',         0,      4,     FixedWidthDec),
            ('uit_in',          4,      2,     FixedWidthDec),	# 01 = check-in
            ('zeroes1',         6,      4,     FixedWidthDec),
            ('company',        10,      8,     OvcCompany),
	]
    _fields00 = [
            ('teller2',        18,      4,     FixedWidthDec),
            ('zeroes2',        22,      6,     FixedWidthDec),
            ('prevbits',       28, 32*8-28,    FixedWidthHex),
        ]
    _fields01 = [
            ('uit_in2',        18,      2,     FixedWidthDec),	# 01 = check-in
            ('teller2',        20,      4,     FixedWidthDec),
            ('zeroes2',        24,      6,     FixedWidthDec),
            ('prevbits',       30, 32*8-30,    FixedWidthHex),
        ]
    # Experimental and not yet correct:
    _fields11 = [
            ('uit_in2',        18,      2,     FixedWidthDec),	# 01 = check-in
            ('teller2',        20,      4,     FixedWidthDec),
            ('zeroes2',        24,      6,     FixedWidthDec),
            ('prevbits',       32, 32*8-32,    FixedWidthHex),
        ]
    _order = [
	    'teller1', 'uit_in', 'zeroes1', 'company', 'uit_in2', 'teller2', 'zeroes2',
	]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

    def parse(self):
	OvcFixedRecord.parse(self)
	if self.uit_in == 0x00:	# maybe uit_in is another "identifier"?
	    self.parse2(self._fields00)
	elif self.uit_in == 0x01:
	    self.parse2(self._fields01)
	elif self.uit_in == 0x02:
	    self.parse2(self._fields11)
	elif self.uit_in == 0x03:
	    self.parse2(self._fields11)
	else:
	    print "Unknown value %x for field uit_in, expected 0 or 1" % self.uit_in
	self.prev = self.mkarray(OvcIndexF50sub, 'prevbits', 18)

    def __str__(self):
        res = "[index_F50_] "
        res += OvcFixedRecord.__str__(self)
	res += "["
	res += ",".join(map(str, self.prev))
	res += "]\n" + tobin(self.data)
        return res

class OvcIndexF70(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('teller1a',         0,      4,     FixedWidthDec),
            ('uit_in',           4,      2,     FixedWidthDec),	# 01 = check-in
            ('zeroes1a',         6,      4,     FixedWidthDec),
            ('company1',        10,      8,     OvcCompany),
            ('in',              18,      2,     FixedWidthDec),	# 01 2 extra bits
            ('teller1b',        20,      4,     FixedWidthDec),
            ('zeroes1b',        24,      6,     FixedWidthDec),
            ('company2',        30,      8,     OvcCompany),	# 18 bits
            ('teller2',         38,      4,     FixedWidthDec), #
            ('zeroes2',         42,      6,     FixedWidthDec), #
            ('company3',        48,      8,     OvcCompany),
            ('teller3',         56,      4,     FixedWidthDec),
            ('zeroes3',         60,      6,     FixedWidthDec),
            ('company4',        66,      8,     OvcCompany),
            ('teller4',         74,      4,     FixedWidthDec),
            ('zeroes4',         78,      6,     FixedWidthDec),
        ]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

    def __str__(self):
        res = "[index_F70_] "
        res += OvcFixedRecord.__str__(self)
        return res

class OvcIndexF10sub(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('type1',           0,       8,     FixedWidthHex),
            ('type2',           8,       6,     FixedWidthHex),
            ('used',            14,      1,     FixedWidthHex),
            ('rest',            15,      2,     FixedWidthHex),
            ('subscr',          17,      4,     OvcSubscriptionId),
        ]
    # type1 and type2 vary by subscription type.

    def __init__(self, data, ovc, offset, **kwargs):
        OvcFixedRecord.__init__(self, data, ovc, offset=offset)

    def __str__(self):
        res = "[subscr]"
        res += OvcFixedRecord.__str__(self)
	if self.type1 != 0:
	    res += ", active"
	    if self.used == 0:
		res += " unused"
	    else:
		res += " and used"
	else:
	    res += ", deactivated"
        return res

class OvcIndexF10(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('size',             0,      4,     FixedWidthDec),
        ]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

	offset = 4
	self.subs = []
	for i in xrange(0, self.size):
	    onesub = OvcIndexF10sub(data, ovc=ovc, offset=offset)
	    self.subs.append(onesub)
	    offset += 21

    def __str__(self):
        res = "[index_F10_] "
        res += OvcFixedRecord.__str__(self)
	for onesub in self.subs:
	    res += "; " + str(onesub)
        return res

class OvcSaldo(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('id',               9,     12,     OvcTransactionId),
            ('idsaldo',      7*8+0,     12,     OvcSaldoTransactionId),
            ('saldo',        9*8+5,     16,     OvcAmountSigned),
            ('unk1',             0,      9,     FixedWidthHex),
            ('unk2',            22,     34,     FixedWidthHex),
            ('unk3',         8*8+4,      8,     FixedWidthHex),
            ('unk4',        11*8+5,     35,     FixedWidthHex),
        ]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

    def __str__(self):
        res = "[saldo_____] "
        res += OvcFixedRecord.__str__(self)
        return res

class OvcSubscriptionAux(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('unk1',             0,   16*8,     FixedWidthHex),
        ]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

    def __str__(self):
        res = "[subscr_aux] "
        res += OvcFixedRecord.__str__(self)
        return res

    @staticmethod
    def addr(slot):
	aux_addr = 0x6c0 + slot * 0x10
	if slot > 2: aux_addr += 0x10	# skip trailer
	return aux_addr

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
                self.field[name] = fieldtype(bits, obj=self, width=width)
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

class OvcVariableTransaction(OvcVariableRecord):
    _fields = [
            # name,           bitmask, width,   type
            ('datetime',         None,  25,     OvcDatetime),
            ('unk24_2',     0x0000002,  24,     FixedWidthHex),
            ('action',      0x0000004,   7,     OvcAction),
            ('company',     0x0000010,  16,     OvcCompany),
            ('transaction', 0x0000040,  24,     OvcTransactionId),      # for credit transactions, this should be OvcSaldoTransactionId
            ('station',     0x0000100,  16,     OvcStation),
            ('machine',     0x0000400,  24,     OvcMachineId),
            ('vehicle',     0x0004000,  16,     OvcVehicleId),
            ('product',     0x0010000,   5,     FixedWidthDec), # product ID ? 5 bits?
            ('unk16_5',     0x0100000,  16,     FixedWidthHex),
            ('amount',      0x0800000,  16,     OvcAmount),
            ('idsubs',      0x2000000,   4,     OvcSubscriptionId),# corresponding subscription
	    #   12 bits instead? or 13 even?
	    # "De eerste 4 bits zijn van de locatie (misschien) en de rest is denk ik het soort subscription dat is gebruikt."
            ('idsubs2',     0x2000000,   9,     FixedWidthHex),
        ]
    _order = [
            'transaction',
            'datetime',
            'action',
            'amount', 
            'company',
	    'station',
	    # the lines are getting too wide but this is ugly too...
	    # ':\n\t\t\t\t\t',
            'machine',
            'vehicle',
            'product',
            'idsubs', ':+', 'idsubs2',
	    ':/',
            'unk24_2',
            'unk16_5',
	]

    def __init__(self, data, ovc):
        OvcVariableRecord.__init__(self, data, ovc)
        self.parse()

    def __str__(self):
        res = '[%02x_%02x_%02x_%x] '%(ord(self.data[0]),ord(self.data[1]),ord(self.data[2]),ord(self.data[3])>>4)
        res += OvcVariableRecord.__str__(self)
        return res

    def parse(self):
	self.field['action'] = OvcAction(0)
        width = OvcVariableRecord.parse(self)
	# Check if this is a credit transaction
	try:
	    if self.action == 0 and self.amount != None and \
		    not ('idsubs' in self.field):
		self.transaction = self.field['transaction'] = OvcSaldoTransactionId(int(self.transaction))
	except AttributeError:
	    pass
	return width

class OvcVariableSubscriptionSub1(OvcVariableSubRecord):
    _fields = [
            # name,           bitmask, width,   type
            ('dt_from',         0x001,  14,     OvcDate),
            ('tm_from',         0x002,  11,     OvcTime),
            ('dt_to',           0x004,  14,     OvcDate),
            ('tm_to',           0x008,  11,     OvcTime),
            ('unk62_1',         0x010,  53,     FixedWidthHex),	# was 62 wide
        ]

    _order = [
            'dt_from',
            'tm_from',
            'dt_to',
            'tm_to',
            'unk62_1',
	]

    def __init__(self, value, obj, **kwargs):
        OvcVariableSubRecord.__init__(self, value, obj=obj, **kwargs)

    def parse(self, start, **kwargs):
        width = OvcVariableSubRecord.parse(self, start=start)
	if 'dt_from' in self.field and not 'tm_from' in self.field:
	    self.field['tm_from'] = OvcTime(-1)
	    self.propagate()
	if 'dt_to' in self.field and not 'tm_to' in self.field:
	    self.field['tm_to'] = OvcTime(-1)
	    self.propagate()
	return width

class OvcVariableSubscription(OvcVariableRecord):
    _fields = [
            # name,           bitmask, width,   type
            ('company',     0x0000200,   8,     OvcCompany),
            ('sub',         0x0000400,  24,     OvcSubscription),
            ('transaction', 0x0000800,  24,     OvcTransactionId),
            ('unk10_1',     0x0002000,  10,     FixedWidthHex),
            ('subfield1',   0x0200000,   9,     OvcVariableSubscriptionSub1),
            ('machine',     0x0800000,  24,     OvcMachineId),
        ]

    _order = [
            'transaction',
            'datetime',
	    #'subfield1',
		'dt_from',
		'tm_from',
		'dt_to',
		'tm_to',
	    'company',
	    'sub',
	    'machine',
	    'unk10_1',
		'unk62_1',
	]

    def __init__(self, data, ovc):
        OvcVariableRecord.__init__(self, data, ovc)
        self.parse()

    def __str__(self):
        res = '[%02x_%02x_%02x_%x] '%(ord(self.data[0]),ord(self.data[1]),ord(self.data[2]),ord(self.data[3])>>4)
        res += OvcVariableRecord.__str__(self)
        return res

#    def parse(self):
#        return OvcVariableRecord.parse(self)

