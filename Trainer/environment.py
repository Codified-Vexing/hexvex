#!/usr/bin/env python

__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

import time
import assembler as ass
from devices import *


class Environ:

	def __init__(self):
		
		# Get time when program starts
		self.START = int(time.time()*100000)
			
		"""Starting Registers
		170
		187
		204
		221
		"""

		# Get widget references
		#self.id = self.builder.get_object("id")
		self.mem = self.builder.get_object("assm_area")
		self.freq_meter = self.builder.get_object("hertz_disp")
		
		# Instantiate HexVex and set which widgets show internal state.
		self.cpu = ass.Core(
							("acc_msb", "acc_lsb", self.builder.get_object("acc_num")),
		
							BLINKER=ass.LED(self.builder.get_object("machine_heartbeat")),
							acc_lsb=ass.Bargraph(self.builder.get_object("acc_lsb").get_children()),
							acc_msb=ass.Bargraph(self.builder.get_object("acc_msb").get_children()),
							cach_lsb=ass.Bargraph(self.builder.get_object("cache_lsb").get_children()),
							cach_msb=ass.Bargraph(self.builder.get_object("cache_msb").get_children()),
							utmr_lsb=ass.Bargraph(self.builder.get_object("utmr_lsb").get_children()),
							utmr_msb=ass.Bargraph(self.builder.get_object("utmr_msb").get_children()),
							)
							
		#Instantiate and setup peripherals		
		devices = [
				#( {"both_addr": 0x0a}, ass.Num_Disp(self.builder.get_object("reg_a")) ),  # Device with only output
				#( {"write_addr": 0x0d}, ass.DipSwitch(self.builder.get_object("dipswt")) ),  # Device with only input
					]	
		for each in devices:
			addrs, obj, connect = each
			self.cpu.add(obj, **addrs)		
		
		# Instantiate and Setup the ALU modules
		#adder, mult, nega, xor, teq,
		modules = {
			0xf1:  # Negate the bits of the Store, Aux Bus is becomes the Least significant part of the result.
				("Boolean NOT",
				"""
out = 0xffff ^ join_byte({2}, {1})
TO_ACCUM(out)
##SETUP LOGIC=
				"""),
			0xf2:  # Performs the XOR operation
				("Boolean XOR",
				"""
out = {2} ^ {1}
TO_ACCUM(out)
##SETUP LOGIC=
				"""),
			0xf3:  # Performs the NOR operation
				("Boolean NOR",
				"""
out = 0xffff ^ ({2} | {1})
TO_ACCUM(out)
##SETUP LOGIC=
				"""),
			0xf4:  # The Right Bitshifter
				("Bitshift Right",
				"""
m = wrap({1},9) # Restrict to 8 binary places
typ = bin({0})[2:].zfill(8)[-2] # 1 if special, 0 if simple
alt = bin({0})[2:].zfill(8)[-1] # If special, 1 is arithmetic shift, 0 is ring shift. If simple, tells what to fill in the gaps with.
lead = str({2})[-m:]
out = bin({2} >> m)[2:].zfill(8)

if typ == "0":
	out = (alt*m)+out[m:]
elif typ == "1":
	pick = (lead, out[m])
	out = pick[alt]+out[m:]
	
out=int(out,2)
TO_ACCUM(out)
##SETUP LOGIC=0
pattern = bin({1})[2:]
TO_MODE(pattern)
				"""),
			0xf5:  # The Left Bitshifter
				("Bitshift Left",
				"""
m = wrap({1},9) # Restrict to 8 binary places
typ = bin({0})[2:].zfill(8)[-2] # 1 if special, 0 if simple
alt = bin({0})[2:].zfill(8)[-1] # If special, 1 is arithmetic shift, 0 is ring shift. If simple, tells what to fill in the gaps with.
lead = str({2})[:m]
out = bin({2} << m)[2:].zfill(8)

if typ == "0":
	out = out[:-m]+(alt*m)
elif typ == "1":
	pick = (lead, (0*m))
	out = out[:-m]+pick[alt]
	
out=int(out,2)
TO_ACCUM(out)

##SETUP LOGIC=0
pattern = bin({1})[2:]
TO_MODE(pattern)
				"""),
			0xf6:  # Addition ALU module
				("Addition",
				"""
out = {2} + {1}
carry = str(int(out > {0}))
TO_FLAGS("xxx"+carry,0)  # Report overflow.
TO_ACCUM(out)

##SETUP LOGIC=0xFF
# Pick which number causes a carry.
TO_MODE({1})
				"""),
			0xf7:  # Multiplication ALU module
				("Multiplication",
				"""
out = {2} * {1}
carry = str(int(out > {0}))
TO_FLAGS("xxx"+carry,0)  # Report overflow.
TO_ACCUM(out)

##SETUP LOGIC=0xFF
# Pick which number causes a carry.
TO_MODE({1})
				"""),
			0xf8:  # Magnitude comparison test for the ALU
				("Test Magnitude",
				"""
eq = str(int({1} == {2}))
gt = str(int({1} > {2}))
# [BOOL, EQAL, GRTR, CRRY]
out = "x"+eq+gt+"x"
TO_FLAGS(out, 0)
##SETUP LOGIC=
				"""),
			}
		for addr, each in modules.items():
			name, logos = each
			inst = ass.ALU(name, logos)
			self.cpu.add(inst, write_addr=addr)

		
	# Example signal handler:
	#def foo(self, widget, data=None):
	#	print("bar")

	def pause(self, widget):
		pass

	def execute(self, widget):
		start = self.mem.get_start_iter()
		end = self.mem.get_end_iter()
		raw_program = self.mem.get_text(start, end, False)
		
		self.cpu(raw_program)
		

	def load_file(self, *foo):
		pass
	def smart_load(self, *foo):
		pass
	def set_numbase(self, *foo):
		pass
	def hide_internals(self, *foo):
		pass
	def hide_state(self, *foo):
		pass

if __name__ == "__main__":
	print("oopsies.")
else:
	pass
