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

    def __init__(self, data):
        self.parsed = False
        self.data = data
        self.field = {}
        self.desc = {}
        self.bits = {}

    def get(self, name):
        return self.field[name]

    def getdata(self):
        return self.data

    def getbits(self, start, length):
        # return number at bit positions of data (0 is beginning)
        return getbits(self.data, start, start+length)

class OvcFixedRecord(OvcNewRecord):
    '''Interpret binary records with fixed data fields. Needs to be subclassed.'''

    def __init__(self, data):
        OvcNewRecord.__init__(self, data)
        self.parse()

    def parse(self):
        self.field = {}
        self.desc = {}
        self.bits = {}
        for field in self._fields:
            name, start, width, fieldtype = field
	    if fieldtype != None:
		bits = self.getbits(start, width)
		#print name, start, width, fieldtype
		self.field[name] = fieldtype(bits, obj=self,width=(width+3)/4)
		self.desc[name] = field
		self.bits[name] = bits
        # everything is ok, incorporate fields
        self.__dict__.update(self.field)
    
    def __str__(self):
        res = ""
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
        for off in xrange(0, width, bitwidth):
            one = self.getbits(start + off, bitwidth)
            arr.append(membertype(one, obj=self, width=(bitwidth+3)/4))
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
            ('ptr0_6_array_1', 4*8,    7*4,     FixedWidthHex),
            ('ptr0_b_array_1', 7*8+4, 12*4,     FixedWidthHex),
	    ('Sbscr:',             0,    0,     None),
            ('subscr_ptrs',   13*8+4, 12*4,     FixedWidthHex),
	    ('Hist:',              0,    0,     None),
            ('history_ptrs',  19*8+4, 10*4,     FixedWidthHex),
           #('ptr0_b_array-3',24*8+4, 12*4,     FixedWidthHex),
	    ('Check:',             0,    0,     None),
            ('check_ptrs',    24*8+4, 12*4,     FixedWidthHex),
            ('recent_credit', 30*8+4,    4,     OvcMostRecentCreditIndex),
            ('unk3',          31*8  ,    8,     FixedWidthHex),
        ]

    def __init__(self, data):
        OvcFixedRecord.__init__(self, data)
        self.history = self.mkarray(HistoryTransactionAddr, 'history_ptrs', 4)
	self.next_history  = find_missing(self.history, 0x0, 0xa)
        self.checks  = self.mkarray(CheckInOutTransactionAddr, 'check_ptrs', 4)
	self.next_check  = find_missing(self.checks, 0x0, 0xc)
        self.checksmyst  = self.mkarray(CheckInOutTransactionAddr, 'ptr0_b_array_1', 4)
	self.next_checkmyst  = find_missing(self.checksmyst, 0x0, 0xc)
	# subscr_ptrs is an ordinary array mapping from subscription index
	# (OvcSubscriptionId) to subscription slot number; first entry is for
	# OvcSubscriptionId = 1.

    def __str__(self):
        res = "[index_FB0_] "
        res += OvcFixedRecord.__str__(self)
        #res += "\n     History (most recent first): " + str(map(str, self.history))
	res += "\n     next in logs               :           %x                                        %x                  %x" % (self.next_checkmyst, self.next_history, self.next_check)
        #res += "\n     Checks                     : " + str(map(str, self.checks))
	#res += "\n     next in checkin/out log    : %x" % self.next_check
	#res += "\n     next in mystery log        : %x" % self.next_checkmyst
        return res

class OvcIndexF50(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            #('company',         14,      4,     OvcCompany),
            #('unk1',             0,     14,     FixedWidthHex),
            #('unk2',            18,32*8-18,     FixedWidthHex),
            ('teller1a',         0,      4,     FixedWidthDec),
            ('uit_in',           4,      2,     FixedWidthDec),	# 01 = check-in
            ('zeroes1a',         6,      4,     FixedWidthDec),
            ('company1',        10,      8,     OvcCompany),
            ('teller1b',        18,      4,     FixedWidthDec),
            ('zeroes1b',        22,      6,     FixedWidthDec),
            ('company2',        28,      8,     OvcCompany),	# 18 bits
            ('teller2',         36,      4,     FixedWidthDec), #
            ('zeroes2',         40,      6,     FixedWidthDec), #
            ('company3',        46,      8,     OvcCompany),
            ('teller3',         54,      4,     FixedWidthDec),
            ('zeroes3',         58,      6,     FixedWidthDec),
            ('company4',        64,      8,     OvcCompany),
            ('teller4',         72,      4,     FixedWidthDec),
            ('zeroes4',         76,      6,     FixedWidthDec),
        ]

    def __init__(self, data):
        OvcFixedRecord.__init__(self, data)

    def __str__(self):
        res = "[index_F50_] "
        res += OvcFixedRecord.__str__(self)
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

    def __init__(self, data):
        OvcFixedRecord.__init__(self, data)

    def __str__(self):
        res = "[index_F70_] "
        res += OvcFixedRecord.__str__(self)
        return res

class OvcIndexF10(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('subscr',           0,      4,     OvcSubscriptionLogIndex),
            ('bitmask',          4,     17,     FixedWidthHex),
            ('unk1',            21,32*8-21,     FixedWidthHex),
        ]
    # bitmask: http://www.ov-chipkaart.org/forum/viewtopic.php?f=10&t=121&sid=9cb9ec29723eca11520748ac6140daa9&start=20#p2402
    # De 0xF10 en 0xF30 velden is het volgt opgebouwd.
    # 4 bit - soort teller/pointer
    # 17 bit - Een soort bitmasker voor de subscriptions
    # --00000011001101001 voor 1ste klasse NS
    # --00000011001110001 voor 2de klasse NS

    def __init__(self, data):
        OvcFixedRecord.__init__(self, data)

    def __str__(self):
        res = "[index_F10_] "
        res += OvcFixedRecord.__str__(self)
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

    def __init__(self, data):
        OvcFixedRecord.__init__(self, data)

    def __str__(self):
        res = "[saldo_____] "
        res += OvcFixedRecord.__str__(self)
        return res

class OvcSubscriptionAux(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('unk1',             0,   16*8,     FixedWidthHex),
        ]

    def __init__(self, data):
        OvcFixedRecord.__init__(self, data)

    def __str__(self):
        res = "[subscrip_2] "
        res += OvcFixedRecord.__str__(self)
        return res

    @staticmethod
    def addr(slot):
	aux_addr = 0x6c0 + slot * 0x10
	if slot > 2: aux_addr += 0x10	# skip trailer
	return aux_addr

class OvcVariableRecord(OvcNewRecord):
    '''Interpret binary records with variable data fields. Needs to be subclassed.'''

    _order = None

    def __init__(self, data):
        OvcNewRecord.__init__(self, data)

    def parse(self, skip):
        self.field = {}
        self.desc = {}
        self.bits = {}
        identifier = self.getbits(0, 28)
        identifier0 = identifier
        prev_field = None
        start = 28 + skip
        for field in self._fields:
            name, mask, width, fieldtype = field
            #print name, mask, width, fieldtype
            if (mask == None) or (identifier & mask):
                # If there are 2 alignment fields in sequence, undo the earlier one.
#                if name == 'unk12_3' and prev_field != None:
#                    prev_name, prev_mask, prev_width, prev_fieldtype = prev_field
#                    if prev_name == 'unk24_2':   # horrible hack
#                        start -= 3
                bits = self.getbits(start, width)
#                print name, start, width, bits
                start += width
                self.field[name] = fieldtype(bits, obj=self, width=(width+3)/4)
                self.desc[name] = field
                self.bits[name] = bits
                if mask != None:
                    identifier = identifier ^ mask
                prev_field = field
        if identifier != 0:
            print "Unknown bits in identifier: %04x (%04x)" % (identifier, identifier0)
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
		#print name, start, width, fieldtype
		if name in self.field:
		    res += str(self.field[name]) + " "
        return res

class OvcVariableTransaction(OvcVariableRecord):
    _fields = [
            # name,           bitmask, width,   type
#            ('datetime',         None,  25,     OvcDatetime),
#            ('unk24_2',     0x0000002,  24,     FixedWidthHex),
#            ('unk3_1',           None,   3,     FixedWidthHex), # alignment?
#            ('action',      0x0000004,   4,     OvcAction),
#            ('unk12_3',          None,  12,     FixedWidthHex), 
#                # for credit transactions, this is smaller, 9 bits?
#                # for add product, this is also 9 bits?
#            ('company',     0x0000010,   4,     OvcCompany),
#            ('ident_4',     0x0000040,  12,     FixedWidthHex), # "identifier"
#            ('transaction',      None,  12,     OvcTransactionId),      # for credit transactions, this should be OvcSaldoTransactionId
#            ('station',     0x0000100,  16,     OvcStation),
#            ('trip_pole',   0x0000400,  24,     OvcMachineId),
#            ('vehicle',     0x0004000,  16,     OvcVehicleId),
#            ('product',     0x0010000,  12,     FixedWidthDec), # product ID ? 5 bits?
#            ('unk16_5',     0x0100000,  16,     FixedWidthHex), # seems to be zeroes
#            ('amount',      0x0800000,  16,     OvcAmount),
#            ('subscription',0x2000000,   4,     OvcSubscriptionId),# corresponding subscription

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
            ('unk16_5',     0x0100000,  16,     FixedWidthHex), # seems to be zeroes
            ('amount',      0x0800000,  16,     OvcAmount),
            ('subscription',0x2000000,   4,     OvcSubscriptionId),# corresponding subscription
            #('rest',             None, 96,     FixedWidthHex), # the unused remaining bits
        ]
    _order = [
            'transaction',
            'datetime',
            'action',
            'amount', 
            'company',
            'station',
            'machine',
            'vehicle',
            'product',
            'subscription',
            'unk24_2',
            'unk16_5',
	]

    def __init__(self, data):
        OvcVariableRecord.__init__(self, data)
        self.parse()
        if not 'action' in self.field:
            self.action = self.field['action'] = OvcAction(0)

    def __str__(self):
        res = '[%02x_%02x_%02x_%x] '%(ord(self.data[0]),ord(self.data[1]),ord(self.data[2]),ord(self.data[3])>>4)
        #res += str(self.datetime) + " "
        res += OvcVariableRecord.__str__(self)
        return res # + "\n"

    def parse(self):
        #self.datetime = OvcDatetime(self.getbits(28, 25))
        OvcVariableRecord.parse(self, 0)
