#!/usr/bin/env python

__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

import time

import assembler as ass

class Environ:

	def __init__(self):
		
		# Get time when program starts
		self.START = int(time.time()*100000)
	
		# Get widget references
		#self.id = self.builder.get_object("id")
		self.mem = self.builder.get_object("prog_mem")
		self.reg_a = self.builder.get_object("reggae")
		self.reg_b = self.builder.get_object("reggie")
		self.reg_c = self.builder.get_object("barman")
		self.dipswt = self.builder.get_object("bouncer")
		self.blinker = self.builder.get_object("machine_heartbeat")
		
		# Instantiate HexVex and set which widgets show internal state.
		self.cpu = ass.Core(
							BLINKER=ass.LED(self.blinker),
							)
		# Setup output devices
		self.cpu.add(ass.Num_Disp(self.reg_a), both_addr=0x0a)
		self.cpu.add(ass.Num_Disp(self.reg_b), both_addr=0x0b)
		self.cpu.add(ass.Bargraph(self.reg_c.get_children()), both_addr=0x0c)
		
		# Instantiate the devices
		dipswt = ass.DipSwitch(self.dipswt)
		
		# Connect input widgets to the HexVex device methods.
		self.dipswt.connect("activate", dipswt.intake)
	
		# Setup input devices
		self.cpu.add(dipswt, both_addr=0x0d)
		
		# Instantiate and Setup the ALU modules
		#adder, mult, nega, xor, teq,
		modules = {
			0x0f1:  # Negate the bits of the Store, Aux Bus is becomes the Least significant part of the result.
				"""
out = 0xffff ^ join_byte({1}, {0})
TO_ACCUM(out)
				""",
			0x0f2:  # Performs the XOR operation
				"""
out = {1} ^ {0}
TO_ACCUM(out)
				""",
			0x0f3:  # Addition ALU module
				"""
out = {1} + {0}
carry = str(int(out > 0xff))
TO_FLAGS("xxx"+carry,0)  # Report a byte overflow.
TO_ACCUM(out)
				""",
			0x0f4:  # Multiplication ALU module
				"""
out = {1} * {0}
carry = str(int(out > 0xffff))
TO_FLAGS("xxx"+carry,0)  # Report a 2-byte overflow.

TO_ACCUM(out)
				""",
			0x0f5:  # Magnitude comparison test for the ALU
				"""
eq = str(int({0} == {1}))
gt = str(int({0} >= {1}))
# [BOOL, EQAL, GRTR, CRRY]
out = "x"+eq+gt+"xx"
TO_FLAGS(out, 0)
				""",
			}
		for addr, logos in modules.items():
			inst = ass.ALU()
			if not logos is None:
				inst.rule = logos
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

if __name__ == "__main__":
	print("oopsies.")
else:
	pass
