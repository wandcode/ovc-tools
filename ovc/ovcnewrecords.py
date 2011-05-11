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

#import re
from util import getbits
from ovctypes import *
from OvcFixedRecord import *
from OvcVariableRecord import *

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
	    ('Subs:',              0,    0,     None),
            ('latest_subscr',    248,    1,     FixedWidthHex),
	    ('InOut:',             0,    0,     None),
            ('latest_travel',    249,    1,     FixedWidthHex),
	    ('Credit:',            0,    0,     None),
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

class OvcIndexF50sub(OvcVariableSubRecord):
    _fields = [
            # name,           bitmask, width,   type
            ('company',          None,   8,     OvcCompany),
            ('status',           0x10,   2,     FixedWidthDec),
            ('index',            None,   4,     CheckInOutTransactionAddrIndex),
            ('unk',              0x20,   4,     FixedWidthHex),
        ]

    def __init__(self, value, obj, **kwargs):
        OvcVariableSubRecord.__init__(self, value, obj=obj, **kwargs)

    def setIndexes(self, typeFB0):
	if 'index' in self.__dict__:
	    self.index.setIndexes(typeFB0)

    def __str__(self):
        res = ""
        res += OvcVariableSubRecord.__str__(self)
	if 'status' in self.__dict__:
	    if self.status == 0x0:
		res += "check-out"
	    elif self.status == 0x1:
		res += "check-in"
	    else:
		res += "???"
        return res

class OvcIndexF50(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('size',         0,      4,     FixedWidthDec),
	]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

    def parse(self):
	OvcFixedRecord.parse(self)
	offset = 4
	self.subs = []
	for i in xrange(0, self.size):
	    identifier = self.getbits(offset, 6)
	    offset += 6
	    onesub = OvcIndexF50sub(identifier, obj=self)
	    width = onesub.parse(offset)
	    self.subs.append(onesub)
	    offset += width

    def setIndexes(self, typeFB0):
	for sub in self.subs:
	    sub.setIndexes(typeFB0)

    def __str__(self):
        res = "[index_F50_] "
        res += OvcFixedRecord.__str__(self)
	res += "["
	res += ",".join(map(str, self.subs))
	res += "]"
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
            ('used',            14,      1,     FixedWidthDec),
            ('rest',            15,      2,     FixedWidthHex),
            ('subscr',          17,      4,     OvcSubscriptionId),
        ]
    # type1 and type2 vary by subscription type.

    def __init__(self, data, ovc, offset, **kwargs):
        OvcFixedRecord.__init__(self, data, ovc, offset=offset)

    def __str__(self):
        res = OvcFixedRecord.__str__(self)
	if self.type1 != 0:
	    res += "active"
	    if self.used == 0:
		res += " but unused"
	    else:
		res += " and used"
	else:
	    res += "deactivated"
        return res

class OvcIndexF10(OvcFixedRecord):
    _fields = [
            #name,           start,  width,     type
            ('size',             0,      4,     FixedWidthDec),
        ]

    def __init__(self, data, ovc):
        OvcFixedRecord.__init__(self, data, ovc)

    def parse(self):
	OvcFixedRecord.parse(self)
	offset = 4
	self.subs = []
	for i in xrange(0, self.size):
	    onesub = OvcIndexF10sub(self.data, ovc=self.ovc, offset=offset)
	    self.subs.append(onesub)
	    offset += 21

    def setIndexes(self, typeFB0):
	for sub in self.subs:
	    sub.setIndexes(typeFB0)

    def __str__(self):
        res = "[index_F10_] "
        res += OvcFixedRecord.__str__(self)
	res += "["
	res += ",".join(map(str, self.subs))
	res += "]"
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
	    # Ontdekking: In de history log: als de waarde 0x004 is, betreft
	    # het de eerste keer dat dit abonnement gebruikt is.
	    # In de checkin/uitlog hebben de bits schijnbaar een andere
	    # betekenis.
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

