#!/usr/bin/env python
"""
States and topologies of HexVex go here.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

from some_functions import *
from devices import *

class Wares:
	
	def __init__(self):
		## SPECIAL DEVICES:

		self.pntr_lsb = Register(self)  # Program pointer or Memory address
		self.pntr_msb = Register(self)  # Program pointer or Memory address
		self.gobak_lsb = Register(self)
		self.gobak_msb = Register(self)
		self.cont_lsb = Register(self)
		self.cont_msb = Register(self)

		self.BLINKER = Flip_Flop(self)  # Shows the system clock state

		self.M_BUS = Register(self)  # Main Bus
		self.A_BUS = Register(self)  # Auxiliary Bus
		self.I_BUS_lsb = Register(self)  # ALU BUS ("I" for "Integration")
		self.I_BUS_msb = Register(self)  # ALU BUS ("I" for "Integration")
		
		self.I_FLAG = Flip_Flop(self)  # Accumulator trigger flag

		# State Registers
		self.RAVN = Flip_Flop(self)
		self.WAIT = Flip_Flop(self)
		#---Checked against instruction conditionals
		self.BOOL = Flip_Flop(self)
		self.EQAL = Flip_Flop(self)
		self.GRTR = Flip_Flop(self)
		self.CRRY = Flip_Flop(self)
		#---
		self.PWM = Flip_Flop(self)
		self.UTMR = Flip_Flop(self)
		# weird ones
		self.JMP = Flip_Flop(self)
		self.SLEEP_START = 0
		#---

		self.cach_lsb = Register(self)
		self.cach_msb = Register(self)

		self.acc_lsb = Register(self)
		self.acc_msb = Register(self)
		self.stmr_lsb = Register(self)
		self.stmr_msb = Register(self)
		self.utmr_lsb = Register(self)
		self.utmr_msb = Register(self)
			
		## :SPECIAL DEVICES
	
	## Signalling functions to internal registers:
	# They are here rather than hxv wiring because quirks in Python would let them 
	# be aware if the Register objects changed to other kind of register.
	
	def I_BUS(self):
		return join_byte(self.I_BUS_msb.get(), self.I_BUS_lsb.get())
	def I_BUS_set(self, inp):
		msb, lsb = split_hex(inp)
		self.I_BUS_lsb.set(lsb)
		self.I_BUS_msb.set(msb)
	
	def PNTR(self):
		return join_byte(self.pntr_msb.get(), self.pntr_lsb.get())
	def PNTR_add(self, inp):
		n = join_byte(self.pntr_msb.get(), self.pntr_lsb.get())
		n += inp
		msb, lsb = split_hex(n)
		self.pntr_lsb.set(lsb)
		self.pntr_msb.set(msb)
	def PNTR_set(self, inp):
		msb, lsb = split_hex(inp)
		self.pntr_lsb.set(lsb)
		self.pntr_msb.set(msb)
	def GOBAK_set(self, inp):
		msb, lsb = split_hex(inp)
		self.gobak_lsb.set(lsb)
		self.gobak_msb.set(msb)
	def GOBAK(self):
		return join_byte(self.gobak_msb.get(), self.gobak_lsb.get())
	def CONT_set(self, inp):
		msb, lsb = split_hex(inp)
		self.cont_lsb.set(lsb)
		self.cont_msb.set(msb)
	def CONT():
		return join_byte(self.cont_msb.get(), self.cont_lsb.get())

	def ACC_set(self, inp):
		msb, lsb = split_hex(inp)
		self.acc_lsb.set(lsb)
		self.acc_msb.set(msb)
	def CACH_set(self, inp):
		msb, lsb = split_hex(inp)
		self.cach_lsb.set(lsb)
		self.cach_msb.set(msb)
	def STMR_set(self, inp):
		msb, lsb = split_hex(inp)
		self.stmr_lsb.set(lsb)
		self.stmr_msb.set(msb)
	def UTMR_set(self, inp):
		msb, lsb = split_hex(inp)
		self.utmr_lsb.set(lsb)
		self.utmr_msb.set(msb)
	def STEP_STMR(self):
		n = join_byte(self.stmr_msb.get(), self.stmr_lsb.get())
		if n <= 0:
			pass
		elif n == 1:
			self.PNTR_set(self.SLEEP_START)
			self.WAIT.reset()
		else:
			n -= 1
		msb, lsb = split_hex(n)
		self.stmr_lsb.set(lsb)
		self.stmr_msb.set(msb)
	def STEP_UTMR(self):
		n = join_byte(self.utmr_msb.get(), self.utmr_lsb.get())
		n += 1
		msb, lsb = split_hex(n)
		self.utmr_lsb.set(lsb)
		self.utmr_msb.set(msb)

	## :Signalling functions to internal registers

