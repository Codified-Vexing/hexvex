#!/usr/bin/env python
"""
Simple stuff used by multiple scripts.
Has to be safe for use in the ALU minilanguage
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "MIT"

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


