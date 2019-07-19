#!/usr/bin/env python
"""
States and topologies of HexVex go here.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

def wrap(inp, limit):
	return inp % limit

def split_hex(inp=0):
	out = wrap(inp, 0x10000)
	out = bin(abs(out))[2:18].zfill(16)
	msb = out[0:8]
	lsb = out[8:16]
	lsb = int(lsb, 2)
	msb = int(msb, 2)
	return (msb, lsb)

def join_byte(msb=0, lsb=0):
	msb = bin(wrap(msb,0x100))[2:10].zfill(8)
	lsb = bin(wrap(lsb,0x100))[2:10].zfill(8)
	out = msb+lsb
	out = int(out, 2)
	return out

## Device primitives:

class Flip_Flop:
	def __init__(self):
		self.value = False
	
	def get(self):
		return self.value
	
	def set(self, val=True):
		if type(val) is int:
			val = bool(int(bin(val)[-1]))
		self.value = val
	
	def reset(self):
		self.set(False)

	def toggle(self):
		self.set(not self.get())
	
	def setup(self):
		pass
		
		
class Register:
	def __init__(self):
		self.value = 0
		self.mirrors = list()
	
	def get(self):
		return self.value
		
	def set(self, inp=None):
		global M_BUS
		if inp is None:
			inp = M_BUS.get()
		self.value = wrap(inp, 0x100)
		
	def update(self):
		for each in self.mirrors:
			each.set()
		
	def setup(self):
		pass


## :Device primitives

## SPECIAL DEVICES:

pntr_lsb = Register()  # Program pointer or Memory address
pntr_msb = Register()  # Program pointer or Memory address
gobak_lsb = Register()
gobak_msb = Register()
cont_lsb = Register()
cont_msb = Register()

BLINKER = Flip_Flop()  # Shows the system clock state

M_BUS = Register()  # Main Bus
A_BUS = Register()  # Auxiliary Bus
I_BUS = Register()  # ALU BUS ("I" for "Integration")
I_FLAG = Flip_Flop()  # Accumulator trigger flag

# State Registers
RAVN = Flip_Flop()
WAIT = Flip_Flop()
#---Checked against instruction conditionals
BOOL = Flip_Flop()
EQAL = Flip_Flop()
GRTR = Flip_Flop()
CRRY = Flip_Flop()
#---
PWM = Flip_Flop()
UTR = Flip_Flop()
# weird ones
JMP = Flip_Flop()
#---

cach_lsb = Register()
cach_msb = Register()

acc_lsb = Register()
acc_msb = Register()
stmr_lsb = Register()
stmr_msb = Register()
utmr_lsb = Register()
utmr_msb = Register()

		
## :SPECIAL DEVICES
