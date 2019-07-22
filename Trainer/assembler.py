#!/usr/bin/env python
"""
This module has all the facilities to interpret HexVex assembly code so thatGTK 
widgets can be actuated by the values of the emulated components and devices.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

# TODO:
# -For devices that take input from widgets, there needs to be events connected
# to these devices' methods. If the devices are eliminated, the bindings need
# to be dealt with somehow.

import configuration as sett
from some_functions import *

from os.path import dirname

condition = {
			"_":(0x0, "not self.I.WAIT.get()"),
			":":(0x1, "self.I.CRRY.get()"),
			"+":(0x2, "self.I.BOOL.get()"),
			"-":(0x3, "not self.I.BOOL.get()"),
			"!":(0x4, "not self.I.EQAL.get()"),
			">":(0x5, "self.I.GRTR.get()"),
			"<":(0x6, "not self.I.GRTR.get()"),
			"=":(0x7, "self.I.EQAL.get()"),
			}

oper = {
		"nhalt":(0x00, "nhalt"),
		"rhalt":(0x01, "rhalt"),
		"chalt":(0x02, "chalt"),
		"ravn":(0x03, "ravn"),
		"poke":(0x04, "poke"),
		"tell":(0x05, "tell"),
		"ngoto":(0x08, "ngoto"),
		"rgoto":(0x09, "rgoto"),
		"cgoto":(0x0a, "cgoto"),
		"cont":(0x0b, "cont"),
		"gobak":(0x0c, "gobak"),
		"rept":(0x0d, "rept"),
		"nmove":(0x10, "nmove"),
		"rmove":(0x11, "rmove"),
		"accfet":(0x12, "accfet"),
		"hexfet":(0x13, "hexfet"),
		"utfet":(0x14, "utfet"),
		"xfeed":(0x15, "xfeed"),
		"fedfet":(0x16, "fedfet"), # Experimental opcode: swaps 16bit values between ALU and Cache
		"whole":(0x17, "whole"), # Experimental opcode: sets all registers to the argument's value
		"!t":(0x24, "toggle"),
		"t>n":(0x25, "nstart"),
		"t>r":(0x26, "rstart"),
		"t>c":(0x27, "cstart"),
		"t+n":(0x28, "nset"),
		"t+r":(0x29, "rset"),
		"t+c":(0x2a, "cset"),
		"pwm":(0x2b, "pwm"),
		}

def instr(inp):
	# Given a memory pointer, figure out the instruction number.
	return int(inp/8)


class Core:
	def __init__(self, internals, **devices):
		self.I = internals
		self.__call__("_nhalt")  # Start with a default program.
		self.g_point = 0  # pointer for «gobak» opcode
		self.c_point = 0  # pointer for «cont» opcode
		self.decoder = [Stage1(self), Stage2(self)]
		# "Read" and "Write" terms are relative to the Bus. The Bus reads the device, and writes to the device.
		# The structure of these is: {addr = [Peripheral1, Peripheral2], }
		self.read = dict()
		self.write = dict()
		# Internal Devices:
		# Updating the status of the device.
		for each, device in devices.items():
			setattr(self.I, each, device)
		
		# To call these by name, use the global variables mentioned.
		# Here we connect the internal devices that can access the Store.
		self.add(self.I.acc_lsb, read_addr=0xda)
		self.add(self.I.acc_msb, read_addr=0xdb)
		self.add(self.I.utmr_lsb, read_addr=0xd1)
		self.add(self.I.utmr_msb, read_addr=0xd2)
		self.add(self.I.cach_lsb, both_addr=0xc1)
		self.add(self.I.cach_msb, both_addr=0xc2)
		
	def __next__(self):
		# Compute an instruction
		DIGITAL_HIGH = self.I.PNTR() % 2 == 0
		if self.I.UTMR.get() and DIGITAL_HIGH:
			self.I.STEP_UTMR()
			
		if self.I.WAIT.get():
			#print("HexVex is halted...")
			if DIGITAL_HIGH:
				self.I.STEP_STMR()
		elif instr(self.I.PNTR()) >= len(self.PROG):
			print("The program is empty!")
			self.decoder[1].nhalt(0)
		else:
			line = self.PROG[instr(self.I.PNTR())]
			permit = eval(line["cond"])
			if permit:
				if self.I.PNTR() % 8 == 0:
					# Cleaning up...
					if self.I.I_FLAG.get():
						self.I.ACC_set(self.I.I_BUS.get())
						self.I.I_FLAG.reset()
					self.I.M_BUS.set(0)
					self.I.A_BUS.set(0)
					self.I.JMP.reset()
				elif self.I.PNTR() % 8 == 2:
					getattr(self.decoder[0], line["opcode"])(line["arg"])
				elif self.I.PNTR() % 8 == 4:
					getattr(self.decoder[1], line["opcode"])(line["arg"])
				elif self.I.PNTR() % 8 == 6:
					pass	

		if not self.I.JMP.get():
			self.I.PNTR_add(1)
		self.I.BLINKER.toggle()
			
	def __call__(self, prog):
		self.stt_reset()
		uvars, subrs, all_instrs, line_num = self.raw_parse(prog)
	
		def arguing(arg=["0",]):
			# This sorts out the instruction arguments during program parsing in a 
			# polymorphic way.
			combo = {**subrs, **uvars}
			msb, lsb = [0, 0]  # works as fall if anything fails
			
			if len(arg) == 1:
				n = combo.get(arg[0], None)
				if n is None:
					n = int(arg[0],0)
				msb, lsb = split_hex(n)
			elif len(arg) == 2:			
				msb = combo.get(arg[0], None)
				if msb is None:
				 	msb = int(arg[0],0)
				lsb = combo.get(arg[1], None)
				if lsb is None:
				 	lsb = int(arg[1],0)
				 	
			return join_byte(msb, lsb)
		
		for pointer, instr in all_instrs.items():
			cond = instr[0]
			instr = instr[1:].split()
			code = instr[0]
			arg = instr[1:]
			arg = arguing(arg)
			human_factor = [instr[1:], split_hex(arg)]
			hx = int(bin(condition[cond][0])[2:].zfill(3) + bin(oper[code][0])[2:].zfill(5) + bin(arg)[2:].zfill(16), 2)
			self.PROG.append({"cond":condition[cond][1], "opcode":oper[code][1], "hex":hx, "mem_addr": pointer, "arg":arg, "arg_human":human_factor})
			print(str(pointer)+":", cond+" "+code, *human_factor[0], "=>", human_factor[1], sep="\t")
		
	def raw_parse(self, prog, line_num=0, uvars=None, subrs=None, other=None):
		
		if uvars is None:
			uvars = dict()
		if subrs is None:
			subrs = dict()
		if other is None:
			other = dict()
		
		# Segregate each line
		prog = prog.split("\n")
		# Sanitize each line
		prog = list(map(lambda x: x.strip(), prog))
		
		for instr in prog:
			found = instr.find("#")
			if found >= 0:
				instr = instr[:found]  # Filter out comments
			instr.strip()
			if len(instr) >= 1: # Ignore empty lines
				cond = instr[0]
				if cond == "|":  # It's an import
					with open(dirname(sett.prog_dir)+"/"+instr[1:]) as fl:
						ext_prog = fl.read()
					added_uvars, added_subrs, added_other, line_num = self.raw_parse(ext_prog, line_num, uvars, subrs, other)
					uvars = {**uvars, **added_uvars}
					subrs = {**subrs, **added_subrs}
					other = {**other, **added_other}
				elif cond == "*":  # It's a variable
					part = instr.split("=")
					# Make sure it's legal var value
					if len(part) == 2:
						# TODO: Can't use «isdigit()» here because the user might
						# ask for other number formats like "0x12". Do a regex
						# check instead?
						uvars[part[0][1:].strip()] = eval(part[1].strip())
					else:
						print("INVALID VARIABLE DEFINITION!")
						break
				elif cond =="[" and instr[-1] == "]":  # It's a goto label
						subrs[instr[1:-1]] = line_num
				else:
					other[line_num] = instr
					line_num += 8

		# Return for when it is on recursion, the higher layers have continuity with lower layers.
		return (uvars, subrs, other, line_num)
		
	def add(self, device, read_addr=None, write_addr=None, both_addr=None):
		# The Bus reads from the device, and writes to the device.
		# Connects a new device to this machine.
		if both_addr:
			read = both_addr
			write = both_addr
		else:
			read = read_addr
			write = write_addr
	
		if read:
			if read in self.read:
				self.read[read].append(device)
			else:
				self.read[read] = [device, ]
		if write:
			if write in self.write:
				self.write[write].append(device)
			else:
				self.write[write] = [device, ]

	def update(self):
		pass
		
	def stt_reset(self):
		self.PROG = list()
		# Pointer keepers
		self.I.PNTR_set(0)
		self.I.GOBAK_set(0)
		self.I.CONT_set(0)
		# Internal Registers
		self.I.M_BUS.set(0)
		self.I.A_BUS.set(0)
		self.I.ACC_set(0)
		self.I.STMR_set(0)
		self.I.UTMR_set(0)
		self.I.CACH_set(0)
		# State Flags
		self.I.RAVN.reset()
		self.I.WAIT.reset()
		self.I.BOOL.reset()
		self.I.EQAL.reset()
		self.I.GRTR.reset()
		self.I.CRRY.reset()
		self.I.PWM.reset()
		self.I.UTMR.reset()
		self.I.JMP.reset()
		print("System has been reset!")


## INSTRUCTION DECODERS:
# Make each opcode return the machine pattern hexes.

class Decoder:
	def __init__(self, core):
		self.c = core
		
	def __getattr__(self, attr):
		print("OPCODE ILLEGAL:", attr)

class Stage1(Decoder):
	##The operations:
	#SYS
	def nhalt(self, inp):
		pass
	def rhalt(self, inp):
		pass
	def chalt(self, inp):
		pass
	def ravn(self, inp):
		pass
	def tell(self, inp):
		addr, num = split_hex(inp)
		self.c.I.A_BUS.set(num)
	#GOTO	
	def ngoto(self, inp):
		msb, lsb = split_hex(inp)
		self.c.I.M_BUS.set(lsb)
		self.c.I.A_BUS.set(msb)
		self.c.I.GOBAK_set(self.c.I.PNTR()-1)
	def rgoto(self, inp):
		self.c.I.M_BUS.set()
		self.c.I.A_BUS.set(self.c.I.acc_lsb.get())
		self.c.I.GOBAK_set(self.c.I.PNTR()-1)
	def cgoto(self, inp):
		self.c.I.GOBAK_set(self.c.I.PNTR()-1)
	def cont(self, inp):
		self.c.I.GOBAK_set(self.c.I.PNTR()-1)
	def gobak(self, inp):
		# Gobak doesn't set itself to go to itself.
		pass
	def rept(self, inp):
		self.c.I.GOBAK_set(self.c.I.PNTR()-1)
	#MOVE
	def nmove(self, inp):
		n, device = split_hex(inp)
		self.c.I.M_BUS.set(n)
		self.c.I.A_BUS.set(self.c.I.acc_lsb.get())
	def rmove(self, inp):
		n = 0
		src_addr, tgt_addr = split_hex(inp)
		tgts = self.c.read.get(src_addr, list())
		if len(tgts) >= 2:
			print("Short circuit between Peripherals detected!")
		for reg in tgts:
			n = n | reg.get()
		self.c.I.M_BUS.set(n)
		self.c.I.A_BUS.set(self.c.I.acc_lsb.get())
	def accfet(self, inp):
		self.c.I.M_BUS.set(self.c.I.acc_lsb.get())
		self.c.I.A_BUS.set(self.c.I.acc_msb.get())
	def hexfet(self, inp):
		msb, lsb = split_hex(inp)
		self.c.I.M_BUS.set(lsb)
		self.c.I.A_BUS.set(msb)
	def utfet(self, inp):
		self.c.I.M_BUS.set(self.c.I.utmr_lsb.get())
		self.c.I.A_BUS.set(self.c.I.utmr_msb.get())
	def xfeed(self, inp):
		pass
	#TIMER
	def toggle(self, inp): pass
	def nstart(self, inp):
		msb, lsb = split_hex(inp)
		self.c.I.M_BUS.set(lsb)
		self.c.I.A_BUS.set(msb)
	def rstart(self, inp):
		bogus, src_addr = split_hex(inp)
		tgts = self.c.read.get(src_addr, list())
		if len(tgts) >= 2:
			print("Short circuit between Peripherals detected!")
		for reg in tgts:
			n = n | reg.get()
		self.c.I.M_BUS.set(n)
	def cstart(self, inp):
		self.c.I.M_BUS.set(self.c.I.cach_lsb.get())
		self.c.I.A_BUS.set(self.c.I.cach_msb.get())
	def nset(self, inp):
		self.nstart(inp)
	def rset(self, inp):
		self.rstart(inp)
	def cset(self, inp):
		self.cstart(inp)
	def pwm(self, inp):
		pass


class Stage2(Decoder):
	##The operations:
	#SYS
	def nhalt(self, inp):
		print("--HEXVEX IS HALTED--")
		self.c.I.STMR_set(inp)
		self.c.I.WAIT.set()
	def poke(self, addr):
		regs = set(self.c.read.get(addr, list()))
		regs |= set(self.c.write.get(addr, list()))
		regs = list(regs)

		for each in regs:
			each.setup()
	def tell(self, inp):
		addr, num = split_hex(inp)
		self.poke(addr)
	#GOTO
	def ngoto(self, inp):
		n = join_byte(self.c.I.A_BUS.get(), self.c.I.M_BUS.get())
		self.c.I.JMP.set()
		self.c.I.PNTR_set(n)
	def gobak(self, inp):
		where = self.c.I.GOBAK + inp
		self.c.I.JMP.set()
		self.c.I.PNTR_set(where)
	#MOVE
	def nmove(self, inp):
		n, addr = split_hex(inp)
		tgts = self.c.write.get(addr, list())
		for each in tgts:
			each.set()
	def rmove(self, inp):
		self.nmove(inp)
	def accfet(self, inp):
		self.c.I.cach_lsb.set(self.c.I.M_BUS.get())
		self.c.I.cach_msb.set(self.c.I.A_BUS.get())
	def hexfet(self, inp):
		self.accfet(inp)
	def utfet(self, inp):
		self.accfet(inp)
	#TIMER
	def toggle(self, inp):
		self.c.I.UTMR.toggle()
	def nstart(self, inp):
		self.c.I.UTMR.set()  # set flag
		n = join_byte(self.c.I.A_BUS.get(), self.c.I.M_BUS.get())
		self.c.I.UTMR_set(n)  # set register
	def rstart(self, inp):
		self.nstart(inp)
	def cstart(self, inp):
		self.nstart(inp)
	def nset(self, inp):
		n = join_byte(self.c.I.A_BUS.get(), self.c.I.M_BUS.get())
		self.c.I.UTMR_set(n)  # set register
	def rset(self, inp):
		self.nset(inp)
	def cset(self, inp):
		self.nset(inp)
	
	
## :INSTRUCTION DECODERS

if __name__ == "__main__":
	print("oopsies.")
