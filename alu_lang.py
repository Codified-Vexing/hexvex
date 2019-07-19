#!/usr/bin/env python
"""
Stuff that enables the minilanguage for the ALU modules to work.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

from hxv_wiring import  wrap, split_hex, join_byte, I_BUS, BOOL, EQAL, GRTR, CRRY

def TO_ACCUM(inp):
	I_BUS.set(wrap(inp, 0x10000))

def TO_FLAGS(pattern, mode):
	pick = ("set", "toggle")
	nam = ["BOOL", "EQAL", "GRTR", "CRRY"]
	flag = [BOOL, EQAL, GRTR, CRRY]
	
	for which, state in enumerate(pattern):
		if state != "x":
			getattr(flag[which], pick[mode])(bool(int(state,2)))
