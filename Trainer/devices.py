#!/usr/bin/env python
"""
Here lies all the classes out of which peripheral devices are defined by.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

from some_functions import *
import some_functions as some  # So the namespace can be referred to by the ALU class.
import configuration as sett
	
## Device primitives:

class Flip_Flop:
	def __init__(self, core):
		self.c = core
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
		
class Bus_Flip_Flop(Flip_Flop):
	def __ini__(self, core, bit_of_interest=0):
		Flip_Flop.__ini__(self, core)
		self.boi=bit_of_interest
		
	def set(self, val=None):
		if val is None:
			val = self.c.M_BUS.get()
			val = bin(val)[:1:-1]
			val = bool(val[self.boi])
		Flip_Flop.set(self, val)
		
class Register:
	def __init__(self, core):
		self.c = core
		self.value = 0
		self.mirrors = list()
	
	def get(self):
		return self.value
		
	def set(self, inp=None):
		if inp is None:
			inp = self.c.M_BUS.get()
		self.value = wrap(inp, 0x100)
		
	def update(self):
		for each in self.mirrors:
			each.set()
		
	def setup(self):
		pass

## :Device primitives


class ALU:
	def __init__(self, core, name="Bogus ALU module", logic="TO_ACCUM({0})##SETUP LOGIC="):
		self.c = core
		self.name = name
		
		self.namespace = {"__builtins__":__builtins__}
		for each in dir(self):
			# Methods of this class which start with "TO_" will be available in the ALU logic minilanguage.
			if each[:3] == "TO_":
				self.namespace[each] = getattr(self, each)
		for each in dir(some):
			# Methods of this class which start with "TO_" will be available in the ALU logic minilanguage.
			if each[:2] != "__":
				self.namespace[each] = getattr(some, each)

		self.rule, m_rule =  logic.split("##SETUP LOGIC=") # Python code with the operation being performed. And how to handle periphlag signal.		
		
		self.mode = None
		self.mode_rule = None
		where = m_rule.find("\n")
		if len(m_rule) >= where:
			try:	
				ini = int(m_rule[:where],0)
				self.mode_rule = m_rule[where:]  # get the actual rule.
				self.setup(ini)  # Get the initial mode
			except:
				print("ALU setup code or initial input is either invalid or empty.")
		
	def set(self, M=None, A=None):
		if M is None:
			M = self.c.M_BUS.get()
		if A is None:
			A = self.c.A_BUS.get()
		result = self.rule.format(self.mode, M, A)  # M = lsb = {1}; A = msb = {2}
		exec(result, self.namespace)
		self.c.I_FLAG.set()
	
	def get(self):
		# ALU modules rarely have a read-the-module address.
		print("ALU module", self.name, "has been invoked")
		return 0
	
	def setup(self, pattern=None):
		if pattern is None:
			pattern = self.c.A_BUS.get()
		exec(self.mode_rule.format(self.mode, pattern), self.namespace)

	def TO_MODE(self, inp):
		# This is a minilanguage keyword. Don't use it otherwise.
		self.mode = inp
		
	def TO_ACCUM(self, inp):
		self.c.I_BUS.set(wrap(inp, 0x10000))

	def TO_FLAGS(self, pattern, mode):
		pick = ("set", "toggle")
		nam = ["BOOL", "EQAL", "GRTR", "CRRY"]
		flag = [self.c.BOOL, self.c.EQAL, self.c.GRTR, self.c.CRRY]
		for which, state in enumerate(pattern):
			if state != "x":
				getattr(flag[which], pick[mode])(bool(int(state,2)))

class LED(Flip_Flop):
	def __init__(self, core, ui_obj):
		# This object takes a GTK_image
		Flip_Flop.__init__(self, core)
		self.pick = ("gtk-media-stop", "gtk-media-record")
		self.do = ui_obj

	def set(self, val=True):
		Flip_Flop.set(self, val)
		self.update()
	
	def update(self):
		self.do.set_from_stock(self.pick[int(self.value)], 4)

class Num_Disp(Register):
	def __init__(self, core, label_obj):
		# This object takes a GTK_labe
		Register.__init__(self, core)
		self.note = ""
		self.disp = label_obj
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
			
	def update(self):
		val = str(self.value)
		self.disp.set_text(val)


class Bargraph(Register):
	def __init__(self, core, lamp_objs):
		# This object takes a list of GTK_image
		Register.__init__(self, core)
		self.pick = ("gtk-media-stop", "gtk-media-record")
		self.bar = lamp_objs

	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
		
	def update(self):
		Register.update(self)
		b = bin(self.value)[2:].zfill(8)
		for digit, led in enumerate(self.bar):
			led.set_from_stock(self.pick[int(b[digit])], 4)
	
	def flip():
		self.display.reverse()


class DipSwitch(Register):
	def __init__(self, core, entry_obj):
		# This object takes a GTK_Entry
		Register.__init__(self, core)
		self.note = ""
		self.entry = entry_obj
		
		entry_obj.connect("activate", self.intake)
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()

	def update(self):
		self.entry.set_text(str(self.value))
	
	def intake(self, widget, signal):
		inp = int(widget.get_text())
		self.set(inp)
		
	
class GPIO(Register):
	def __init__(self, core, label_obj, mode_indicator):
		# This object takes a GTK_entry
		Register.__init__(self, core)
		self.pick = ("gtk-fullscreen", "gtk-leave-fullscreen")
		self.note = ""
		self.mode = False  # False = Readable device; True = Written-to device
		self.disp = label_obj
		self.LED = mode_indicator
		
		disp.connect("activate", self.intake)
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
	
	def setup(self):
		pattern = bin(self.c.A_BUS.get())[-2:]
		pick = {"00":self.mode, "01":not self.mode, "10":False, "11": True}
		self.mode = pick[pattern]
	
	def update(self):
		self.disp.set_text(str(self.value))
		self.LED.set_from_stock(self.pick[int(self.value)], 4)

	def intake(self, widget, signal):
		if not mode:
			inp = int(widget.get_text())
			self.set(inp)

class Piano(GPIO):
	def __init__(self, core, button_objs):
		# This object takes a list of GTK_Buttons
		GPIO.__init__(self, core)
		self.timbre = "Piano"
	
	def set(self, inp=None):
		GPIO.set(self,inp)
		# Play note


## Weird ones:
class TackOnSTT:
	def __init__(self, msb, lsb, label_obj):
		self.msb = msb
		self.lsb = lsb
		self.disp = label_obj
		self.set()
		
	def set(self):
		val = join_byte(self.msb.get(), self.lsb.get())
		if sett.hex_format_stt:
			self.disp.set_text(hex(val)[2:].zfill(4))
		else:
			self.disp.set_text(str(val).zfill(5))


