#!/usr/bin/env python
"""
Configs and settings.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

prog_dir = "progs/"
open_last_save = False
save_with_exec = False
max_hz = 100
mid_hz = 12  # Doesn't do anything yet.
CLK = 2  # in Hertz, the initial clock speed

hex_format_reg = False  # Doesn't do anything yet.
hex_format_stt = False  # Doesn't do anything yet.
pane_handle_position = 300

default_peripherals = (
	# read address, write address, device kind, initial value, args
	(None, 0x01, "Bargraph", 0b01010101, ("A Binary Display", )),
	(0xaa, 0xaa, "GPIO", 0, ("io_a",)),
	(0xbb, 0xbb, "GPIO", 0, ("io_b",)),
	(0xcc, 0xcc, "GPIO", 0, ("io_c",)),
	(0xdd, 0xdd, "GPIO", 0, ("io_d",)),
					)
default_alu = {
	# write address: (comment, logic code)
		0xf0:("Move to Accumulator", 
		"""
out = {1}
TO_ACCUM(out)
##SETUP LOGIC=
		"""),
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
		0xf9:  # Magnitude comparison test for the ALU
			("Number Negator",
			"""
out = 0xffff ^ {1}
out = out + 1
TO_ACCUM(out)
##SETUP LOGIC=
			"""),				
		}
