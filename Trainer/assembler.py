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

PNTR = 0  # Program pointer or Memory address

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
	out = bin(inp)[2:18].zfill(16)
	out1 = out[0:8]
	out2 = out[8:16]
	out1 = int(out1, 2)
	out2 = int(out2, 2)
	return (out1, out2)

def join_byte(inp1=0, inp2=0):
	out1 = bin(wrap(inp1,0x100))[2:10].zfill(8)
	out2 = bin(wrap(inp2,0x100))[2:10].zfill(8)
	out = out1+out2
	out = int(out, 2)
	return out


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
		self.rule = "TO_ACCUM({})"  # Python code with the operation being performed.

	def set(self, inp=None):
		if inp is None:
			inp = M_BUS.get()
		result = self.rule.format(inp)
		I_BUS = eval(result)
		I_FLAG.set()
	def get(self):
		# ALU modules rarely have a read-the-module address.
		pass

## :PERIPHERAL DEVICES
## SPECIAL DEVICES:

BLINK = Flip_Flop()  # Shows the system clock state

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

acc_lsb = Register()
acc_msb = Register()
def TO_ACCUM(inp):
	lsb, msb = split_hex(inp)
	acc_lsb.set(lsb)
	acc_msb.set(msb)
stmr_lsb = Register()
stmr_msb = Register()
def TO_STMR(inp):
	lsb, msb = split_hex(inp)
	stmr_lsb.set(lsb)
	stmr_msb.set(msb)
def STEP_STMR():
	n = join_byte(stmr_lsb.get(), stmr_msb.get())
	if n == 0:
		pass
	elif n == 1:
		WAIT.reset()
	else:
		n -= 1
	lsb, msb = split_hex(n)
	stmr_lsb.set(lsb)
	stmr_msb.set(msb)
	
## :SPECIAL DEVICES

class Core:
	def __init__(self, **devices):
		self.__call__("_nhalt")  # Start with a default program.
		self.instr = 0  # Remember to check the proper instruction when jumping because pointers don't match program lines.
		self.g_point = 0  # pointer for «gobak» opcode
		self.c_point = 0  # pointer for «cont» opcode
		self.decoder = [Decoder1(self), Decoder2(self)]
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
		global PNTR
			
		if WAIT.get():
			print("HexVex is halted...")
			STEP_STMR()
		elif self.instr >= len(self.PROG):
			# the program is empty.
			print("The program is empty!")
			self.decoder[0].nhalt(0)
		else:
			permit = eval(self.PROG[self.instr]["cond"])
			if permit:
				if PNTR % 7 == 0:
					getattr(self.decoder[0], self.PROG[self.instr]["opcode"])(self.PROG[self.instr]["arg"])
				elif PNTR % 7 == 2:
					getattr(self.decoder[1], self.PROG[self.instr]["opcode"])(self.PROG[self.instr]["arg"])
				elif PNTR % 7 == 4:
					pass
			if PNTR % 7 == 6:
					M_BUS.set(0)
					A_BUS.set(0)
					self.instr += 1					
			if I_FLAG.get():
				TO_ACCUM(I_BUS)
				I_FLAG.reset()
		
		PNTR += 1
		BLINK.toggle()
			
	def __call__(self, prog, line_num=0):
		# Parse a program
		global PNTR
		if line_num == 0:
			# Means it's a new program so we have to clear the old one.
			self.stt_reset()
			
		uvars = dict()
		subrs = dict()
		
		def arguing(inp1="0", inp2="0"):
			# This sorts out the instruction arguments during program parsing in a 
			# polymorphic way.
			inp1 = uvars.get(inp1, subrs.get(inp1, eval(inp1)))
			inp2 = uvars.get(inp2, subrs.get(inp2, eval(inp2)))

			return join_byte(inp1, inp2)
			
				
		# Get each instruction from each line
		prog = prog.split("\n")
		# Sanitize each line
		prog = list(map(lambda x: x.strip(), prog))
		
		for instr in prog:
			line_num += 1
			found = instr.find("#")
			if found >= 0:
				instr = instr[:found]  # Filter out comments
			instr.strip()
			if len(instr) >= 1: # Ignore empty lines
				cond = instr[0]
				if cond == "|":  # It's an import
					with open(dirname(prog_dir)+"/"+cond[1:]) as fl:
						ext_prog = fl.read()
					added_uvars, added_subrs, line_num = self.parse(ext_prog, line_num-1)
					uvars = {**uvars, **added_uvars}
					subrs = {**subrs, **added_subrs}
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
				elif cond =="[" and cond[-1] == "]":  # It's a goto label
						subrs[cond[1:-1]] = line_num
				else:
					instr = instr[1:].split()
					code = instr[0]
					arg = arguing(*instr[1:])
					hx = int(bin(condition[cond][0])[2:].zfill(3) + bin(oper[code][0])[2:].zfill(5) + bin(arg)[2:].zfill(16), 2)
					self.PROG.append({"cond":condition[cond][1], "opcode":oper[code][1], "arg":arg, "hex":hx})

		# Return for when it is on recursion, the higher layers have continuity with lower layers.
		return (uvars, subrs, line_num)
		
	def add(self, device, read_addr=None, write_addr=None, both_addr=None):
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
		global PNTR
		self.PROG = list()
		PNTR = 0
		self.instr = 0
		# State Registers
		RAVN.reset()
		WAIT.reset()
		BOOL.reset()
		EQAL.reset()
		GRTR.reset()
		CRRY.reset()
		PWM.reset()
		UTR.reset()
		print("System has been reset!")


## INSTRUCTION DECODERS:
# Make each opcode return the machine pattern hexes.

class Decoder1:
	def __init__(self, core):
		self.core = core
	def __getattr__(self, val):
		print("OPCODE ILLEGAL")
	##The operations:
	#SYS
	def nhalt(self, inp):
		TO_STMR(inp)
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
		pass
	def rgoto(self, inp):
		pass
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


class Decoder2:
	def __init__(self, core):
		self.core = core
	def __getattr__(self, val):
		pass
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
