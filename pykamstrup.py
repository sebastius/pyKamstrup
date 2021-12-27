#!/usr/local/bin/python3
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <phk@FreeBSD.ORG> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
# ----------------------------------------------------------------------------
#

from __future__ import print_function

# You need pySerial 
import serial
import math
import subprocess

#######################################################################
# These are the variables I have managed to identify
# Submissions welcome.
# disabled several that have no use in my setup

kamstrup_MC602_var = {
#1003:   "DATE",
60:	"E1",
#94:	"E2",
63:	"E3",
#61:	"E4",
#62:	"E5",
#95:	"E6",
#96:	"E7",
97:	"E8",
110:	"E9",
#64:	"TA2",
#65:	"TA3",
68:	"V1",
#69:	"V2",
84:	"VA",
#85:	"VB",
72:	"M1",
#73:	"M2",
1004:	"HR",
113:	"INFOEVENT",
#1002:	"CLOCK",
99:	"INFO",
86:	"T1",
87:	"T2",
#88:	"T3",
#122:"T4",
89:	"T1-T2",
#91:	"P1",
#92:	"P2",
74:	"FLOW1",
75:	"FLOW2",
80:	"EFFEKT1",
#123:	"MAX_FLOW1DATE",
#124:	"MAX_FLOW1",
#125:	"MIN_FLOW1DATE",
#126:	"MIN_FLOW1",
#127:	"MAX_EFFEKT1DATE",
#128:	"MAX_EFFEKT1",
#129:	"MIN_EFFEKT1DATE",
#130:	"MIN_EFFEKT1",
#138:	"MAX_FLOW1DATE",
#139:	"MAX_FLOW1",
#140:	"MIN_FLOW1DATE",
#141:	"MIN_FLOW1",
#142:	"MAX_EFFEKT1DATE",
#143:	"MAX_EFFEKT1",
#144:	"MIN_EFFEKT1DATE",
#3145:	"MIN_EFFEKT1",
#146:	"AVR_T1",
#147:	"AVR_T2",
#149:	"AVR_T1",
#150:	"AVR_T2",
#66:	"TL2",
#67:	"TL3",
#98:	"XDAY",
#152:	"PROG_NO",
#153:	"CONFIG_NO_1",
#168:	"CONFIG_NO_2",
#1001:	"SERIE_NO",
#112:	"METER_NO_2",
#1010:	"METER_NO_1",
#114:	"METER_NO_VA",
#104:	"METER_NO_VB",
#1005:	"METER_TYPE",
#154:	"CHECK_SUM_1",
#155:	"HIGH_RES",
#157:	"TOPMODUL_ID",
#158:	"BOTMODUL_ID",
175:	"INFOHOUR",
#234:	"IMPINa",
#235:	"IMPINb",
}

#######################################################################
# Units, provided by Erik Jensen

units = {
	0: '', 1: 'Wh', 2: 'kWh', 3: 'MWh', 4: 'GWh', 5: 'j', 6: 'kj', 7: 'Mj',
	8: 'Gj', 9: 'Cal', 10: 'kCal', 11: 'Mcal', 12: 'Gcal', 13: 'varh',
	14: 'kvarh', 15: 'Mvarh', 16: 'Gvarh', 17: 'VAh', 18: 'kVAh',
	19: 'MVAh', 20: 'GVAh', 21: 'kW', 22: 'kW', 23: 'MW', 24: 'GW',
	25: 'kvar', 26: 'kvar', 27: 'Mvar', 28: 'Gvar', 29: 'VA', 30: 'kVA',
	31: 'MVA', 32: 'GVA', 33: 'V', 34: 'A', 35: 'kV',36: 'kA', 37: 'C',
	38: 'K', 39: 'l', 40: 'm3', 41: 'l/h', 42: 'm3/h', 43: 'm3xC',
	44: 'ton', 45: 'ton/h', 46: 'h', 47: 'hh:mm:ss', 48: 'yy:mm:dd',
	49: 'yyyy:mm:dd', 50: 'mm:dd', 51: '', 52: 'bar', 53: 'RTC',
	54: 'ASCII', 55: 'm3 x 10', 56: 'ton x 10', 57: 'GJ x 10',
	58: 'minutes', 59: 'Bitfield', 60: 's', 61: 'ms', 62: 'days',
	63: 'RTC-Q', 64: 'Datetime'
}

#######################################################################
# Kamstrup uses the "true" CCITT CRC-16
#

def crc_1021(message):
		poly = 0x1021
		reg = 0x0000
		for byte in message:
				mask = 0x80
				while(mask > 0):
						reg<<=1
						if byte & mask:
								reg |= 1
						mask>>=1
						if reg & 0x10000:
								reg &= 0xffff
								reg ^= poly
		return reg

#######################################################################
# Byte values which must be escaped before transmission
#

escapes = {
	0x06: True,
	0x0d: True,
	0x1b: True,
	0x40: True,
	0x80: True,
}

#######################################################################
# And here we go....
#
class kamstrup(object):

	def __init__(self, serial_port = "/dev/ttyKamstrup"):
		self.debug_fd = open("/tmp/_kamstrup", "a")
		self.debug_fd.write("\n\nStart\n")
		self.debug_id = None

		self.ser = serial.Serial(
			port = serial_port,
			baudrate = 1200,
			timeout = 1.0)

	def debug(self, dir, b):
		for i in b:
			if dir != self.debug_id:
				if self.debug_id != None:
					self.debug_fd.write("\n")
				self.debug_fd.write(dir + "\t")
				self.debug_id = dir
			self.debug_fd.write(" %02x " % i)
		self.debug_fd.flush()

	def debug_msg(self, msg):
		if self.debug_id != None:
			self.debug_fd.write("\n")
		self.debug_id = "Msg"
		self.debug_fd.write("Msg\t" + msg)
		self.debug_fd.flush()

	def wr(self, b):
		b = bytearray(b)
		self.debug("Wr", b);
		self.ser.write(b)

	def rd(self):
		a = self.ser.read(1)
		if len(a) == 0:
			self.debug_msg("Rx Timeout")
			return None
		b = bytearray(a)[0]
		self.debug("Rd", bytearray((b,)));
		return b

	def send(self, pfx, msg):
		b = bytearray(msg)

		b.append(0)
		b.append(0)
		c = crc_1021(b)
		b[-2] = c >> 8
		b[-1] = c & 0xff

		c = bytearray()
		c.append(pfx)
		for i in b:
			if i in escapes:
				c.append(0x1b)
				c.append(i ^ 0xff)
			else:
				c.append(i)
		c.append(0x0d)
		self.wr(c)

	def recv(self):
		b = bytearray()
		while True:
			d = self.rd()
			if d == None:
				return None
			if d == 0x40:
				b = bytearray()
			b.append(d)
			if d == 0x0d:
				break
		c = bytearray()
		i = 1;
		while i < len(b) - 1:
			if b[i] == 0x1b:
				v = b[i + 1] ^ 0xff
				if v not in escapes:
					self.debug_msg(
						"Missing Escape %02x" % v)
				c.append(v)
				i += 2
			else:
				c.append(b[i])
				i += 1
		if crc_1021(c):
			self.debug_msg("CRC error")
		return c[:-2]

	def readvar(self, nbr):
		# I wouldn't be surprised if you can ask for more than
		# one variable at the time, given that the length is
		# encoded in the response.  Havn't tried.

		self.send(0x80, (0x3f, 0x10, 0x01, nbr >> 8, nbr & 0xff))

		b = self.recv()
		if b == None:
			return (None, None)

		if len(b) == 2:
			return(None, None)

		if b[0] != 0x3f or b[1] != 0x10:
			return (None, None)

		if b[2] != nbr >> 8 or b[3] != nbr & 0xff:
			return (None, None)

		if b[4] in units:
			u = units[b[4]]
		else:
			u = None

		# Decode the mantissa
		x = 0
		for i in range(0,b[5]):
			x <<= 8
			x |= b[i + 7]

		# Decode the exponent
		i = b[6] & 0x3f
		if b[6] & 0x40:
			i = -i
		i = math.pow(10,i)
		if b[6] & 0x80:
			i = -i
		x *= i

		if False:
			# Debug print
			s = ""
			for i in b[:4]:
				s += " %02x" % i
			s += " |"
			for i in b[4:7]:
				s += " %02x" % i
			s += " |"
			for i in b[7:]:
				s += " %02x" % i

			print(s, "=", x, units[b[4]])

		return (x, u)
			

if __name__ == "__main__":

	import time

	foo = kamstrup()
	while (1):
		for i in kamstrup_MC602_var:
			x,u = foo.readvar(i)
			print("%-25s" % kamstrup_MC602_var[i], x, u)
			subprocess.run(
				[
					"mqtt-simple",
					"-h",
					"houseparty.local",
					"-p",
					"kamstrup/"+kamstrup_MC602_var[i],
					"-m",
                   str(x)+" "+str(u),
				]
			)
		time.sleep(5)
