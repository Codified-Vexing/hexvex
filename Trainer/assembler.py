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
# -Make the global stuff into an encapsulated class, maybe?

from os.path import dirname

## CONFIGURATION:
prog_dir = "progs/"
## :CONFIGURATION

condition = {
			"_":(0x0, "not WAIT.get()"),
			":":(0x1, "CRRY.get()"),
			"+":(0x2, "BOOL.get()"),
			"-":(0x3, "not BOOL.get()"),
			"!":(0x4, "not EQAL.get()"),
			">":(0x5, "GRTR.get()"),
			"<":(0x6, "not GRTR.get()"),
			"=":(0x7, "EQAL.get()"),
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
		"!t":(0x24, "toggle"),
		"t>n":(0x25, "nstart"),
		"t>r":(0x26, "rstart"),
		"t>c":(0x27, "cstart"),
		"t+n":(0x28, "nset"),
		"t+r":(0x29, "rset"),
		"t+c":(0x2a, "cset"),
		"pwm":(0x2b, "pwm"),
		}
		
def wrap(inp, limit):
	return inp % limit

def split_hex(inp=0):
	out = bin(abs(inp))[2:18].zfill(16)
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

def instr(inp):
	# Given a memory pointer, figure out the instruction number.
	return int(inp/8)

## PERIPHERAL DEVICES:

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
	
	def get(self):
		return self.value
		
	def set(self, inp=None):
		global M_BUS
		if inp is None:
			inp = M_BUS.get()
		self.value = wrap(inp, 0x100)
		
	def setup(self):
		pass


class LED(Flip_Flop):
	def __init__(self, ui_obj):
		Flip_Flop.__init__(self)
		self.pick = ("gtk-media-stop", "gtk-media-record")
		self.do = ui_obj

	def set(self, val=True):
		Flip_Flop.set(self, val)
		self.update()
	
	def update(self):
		self.do.set_from_stock(self.pick[int(self.value)], 4)

class Num_Disp(Register):
	def __init__(self, label_obj):
		Register.__init__(self)
		self.note = ""
		self.disp = label_obj
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
			
	def update(self):
		self.disp.set_text(str(self.value))		


class Bargraph(Register):
	def __init__(self, label_objs):
		Register.__init__(self)
		self.pick = ("gtk-media-stop", "gtk-media-record")
		self.disp = label_objs
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
		
	def update(self):
		b = bin(self.value)[2:].zfill(8)
		for digit, led in enumerate(self.disp):
			led.set_from_stock(self.pick[int(b[digit])], 4)


class DipSwitch(Register):
	def __init__(self, entry_obj):
		Register.__init__(self)
		self.note = ""
		self.entry = entry_obj
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()

	def update(self):
		self.entry.set_text(str(self.value))
	
	def intake(self, widget):
		inp = int(widget.get_text())
		self.set(inp)
		
	
class GPIO(Register):
	def __init__(self, label_obj, mode_indicator):
		Register.__init__(self)
		self.pick = ("gtk-fullscreen", "gtk-leave-fullscreen")
		self.note = ""
		self.mode = False  # False = Readable device; True = Written-to device
		self.disp = label_obj
		self.LED = mode_indicator
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
	
	def setup(self):
		pattern = bin(A_BUS)[-2:]
		pick = {"00":self.mode, "01":not self.mode, "10":False, "11": True}
		self.mode = pick[pattern]
	
	def update(self):
		self.disp.set_text(str(self.value))
		self.LED.set_from_stock(self.pick[int(self.value)], 4)


class ALU:
	def __init__(self):
		self.name = "Bogus ALU module"
		self.rule = "TO_ACCUM({0})"  # Python code with the operation being performed.

	def set(self, M=None, A=None):
		if M is None:
			M = M_BUS.get()
		if A is None:
			A = A_BUS.get()
		result = self.rule.format(M, A)  # M = lsb = {0}; A = msb = {1}
		exec(result)
		I_FLAG.set()
	def get(self):
		# ALU modules rarely have a read-the-module address.
		pass

## :PERIPHERAL DEVICES
## SPECIAL DEVICES:


pntr_lsb = Register()  # Program pointer or Memory address
pntr_msb = Register()  # Program pointer or Memory address
def PNTR_add(inp):
	n = join_byte(pntr_msb.get(), pntr_lsb.get())
	n += inp
	msb, lsb = split_hex(n)
	pntr_lsb.set(lsb)
	pntr_msb.set(msb)
def PNTR_set(inp):
	msb, lsb = split_hex(inp)
	pntr_lsb.set(lsb)
	pntr_msb.set(msb)
def PNTR():
	return join_byte(pntr_msb.get(), pntr_lsb.get())

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
def ACC_set(inp):
	msb, lsb = split_hex(inp)
	acc_lsb.set(lsb)
	acc_msb.set(msb)
def STMR_set(inp):
	msb, lsb = split_hex(inp)
	stmr_lsb.set(lsb)
	stmr_msb.set(msb)
def TO_UTMR(inp):
	msb, lsb = split_hex(inp)
	utmr_lsb.set(lsb)
	utmr_msb.set(msb)
def STEP_STMR():
	n = join_byte(stmr_msb.get(), stmr_lsb.get())
	if n == 0:
		pass
	elif n == 1:
		WAIT.reset()
	else:
		n -= 1
	msb, lsb = split_hex(n)
	stmr_lsb.set(lsb)
	stmr_msb.set(msb)
def STEP_UTMR():
	n = join_byte(utmr_msb.get(), utmr_lsb.get())
	n += 1
	msb, lsb = split_hex(n)
	utmr_lsb.set(lsb)
	utmr_msb.set(msb)
		
## :SPECIAL DEVICES

## ALU minilanguage keywords:

def TO_ACCUM(inp):
	I_BUS.set(inp)

def TO_FLAGS(pattern, mode):
	pick = ("set", "toggle")
	flag = [BOOL, EQAL, GRTR, CRRY]
	for which, state in enumerate(pattern):
		if state != "x":
			getattr(flag[which], pick[mode])(bool(state))

## :ALU minilanguage keywords


class Core:
	def __init__(self, **devices):
		self.__call__("_nhalt")  # Start with a default program.
		self.g_point = 0  # pointer for «gobak» opcode
		self.c_point = 0  # pointer for «cont» opcode
		self.decoder = [Stage1(self), Stage2(self)]
		# "Read" and "Write" terms are relative to the Bus. The Bus reads the device, and writes to the device.
		# The structure of these is: {addr = [Peripheral1, Peripheral2], }
		self.read = dict()
		self.write = dict()
		
		# Internal Devices:
		for each, device in devices.items():
			globals()[each] = device
		# To call these by name, use the global variables mentioned.
		# Here we connect the internal devices that can access the Store.
		self.add(acc_lsb, read_addr=0xda)
		self.add(acc_msb, read_addr=0xdb)
		
	def __next__(self):
		# Compute an instruction
		if WAIT.get():
			print("HexVex is halted...")
			STEP_STMR()
		elif instr(PNTR()) >= len(self.PROG):
			# the program is empty.
			print("The program is empty!")
			self.decoder[0].nhalt(0)
		else:
			line = self.PROG[instr(PNTR())]
			permit = eval(line["cond"])
			if permit:
				if PNTR() % 8 == 0:
					# Cleaning up...
					if I_FLAG.get():
						ACC_set(I_BUS.get())
						I_FLAG.reset()
					M_BUS.set(0)
					A_BUS.set(0)
					JMP.reset()
				elif PNTR() % 8 == 2:
					getattr(self.decoder[0], line["opcode"])(line["arg"])
				elif PNTR() % 8 == 4:
					getattr(self.decoder[1], line["opcode"])(line["arg"])
				elif PNTR() % 8 == 6:
					pass	

		if not JMP.get():
			PNTR_add(1)
		BLINKER.toggle()
			
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
					with open(dirname(prog_dir)+"/"+instr[1:]) as fl:
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
		PNTR_set(0)
		M_BUS.set(0)
		A_BUS.set(0)
		ACC_set(0)
		STMR_set(0)
		TO_UTMR(0)
		# State Registers
		RAVN.reset()
		WAIT.reset()
		BOOL.reset()
		EQAL.reset()
		GRTR.reset()
		CRRY.reset()
		PWM.reset()
		UTR.reset()
		JMP.reset()
		print("System has been reset!")


## INSTRUCTION DECODERS:
# Make each opcode return the machine pattern hexes.

class Decoder:
	def __init__(self, core):
		self.core = core
	def __getattr__(self, attr):
		print("OPCODE ILLEGAL")

class Stage1(Decoder):
	##The operations:
	#SYS
	def nhalt(self, inp):
		STMR_set(inp)
		WAIT.set()
	def rhalt(self, inp):
		pass
	def chalt(self, inp):
		pass
	def ravn(self, inp):
		pass
	def tell(self, inp):
		addr, num = split_hex(inp)
		A_BUS.set(num)
	#GOTO	
	def ngoto(self, inp):
		msb, lsb = split_hex(inp)
		M_BUS.set(lsb)
		A_BUS.set(msb)
	def rgoto(self, inp):
		M_BUS.set()
		A_BUS.set(acc_lsb.get())
	def cgoto(self, inp):
		pass
	def cont(self, inp):
		pass
	def gobak(self, inp):
		pass
	def rept(self, inp):
		pass
	#MOVE
	def nmove(self, inp):
		n, device = split_hex(inp)
		M_BUS.set(n)
		A_BUS.set(acc_lsb.get())
	def rmove(self, inp):
		n = 0
		src_addr, tgt_addr = split_hex(inp)
		tgts = self.core.read.get(src_addr, list())
		if len(tgts) >= 2:
			print("Short circuit between Peripherals detected!")
		for reg in tgts:
			n = n | reg.get()
		M_BUS.set(n)
		A_BUS.set(acc_lsb.get())
	def accfet(self, inp):
		pass
	def hexfet(self, inp):
		pass
	def utfet(self, inp):
		pass
	def xfeed(self, inp):
		pass
	#TIMER
	def toggle(self, inp):
		pass
	def nstart(self, inp):
		pass
	def rstart(self, inp):
		pass
	def cstart(self, inp):
		pass
	def nset(self, inp):
		pass
	def rset(self, inp):
		pass
	def cset(self, inp):
		pass
	def pwm(self, inp):
		pass


class Stage2(Decoder):
	##The operations:
	#SYS
	def poke(self, addr):
		regs = set(self.core.read.get(addr, list()))
		regs ^= set(self.core.write.get(addr, list()))
		regs = list(regs)

		for each in regs:
			each.setup()
	def tell(self, inp):
		addr, num = split_hex(inp)
		self.poke(addr)
	#GOTO
	def ngoto(self, inp):
		n = join_byte(A_BUS.get(), M_BUS.get())
		JMP.set()
		PNTR_set(n)
	#MOVE
	def nmove(self, inp):
		n, addr = split_hex(inp)
		tgts = self.core.write.get(addr, list())
		for each in tgts:
			each.set()
	def rmove(self, inp):
		self.nmove(inp)
	#TIMER
	
## :INSTRUCTION DECODERS


if __name__ == "__main__":
	print("oopsies.")
