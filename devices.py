#!/usr/bin/env python
"""
Here lies all the classes out of which peripheral devices are defined by.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

from hxv_wiring import wrap, split_hex, join_byte, Flip_Flop, Register, M_BUS, A_BUS, I_BUS, I_FLAG
import alu_lang as alu
	

class ALU:
	def __init__(self, name="Bogus ALU module", logic="TO_ACCUM({0})##SETUP LOGIC="):
		self.name = name
		
		self.namespace = {"__builtins__": alu.__builtins__, "TO_MODE": self.TO_MODE}
		for each in dir(alu):
			if each[:2] != "__":
				self.namespace[each] = getattr(alu, each)

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
				print("ALU setup code or input is invalid.")
		
	def set(self, M=None, A=None):
		if M is None:
			M = M_BUS.get()
		if A is None:
			A = A_BUS.get()
		result = self.rule.format(self.mode, M, A)  # M = lsb = {1}; A = msb = {2}
		exec(result, self.namespace)
		I_FLAG.set()
	
	def get(self):
		# ALU modules rarely have a read-the-module address.
		print("ALU module", self.name, "has been invoked")
		return 0
	
	def setup(self, pattern=None):
		if pattern is None:
			pattern = A_BUS.get()
		exec(self.mode_rule.format(self.mode, pattern), self.namespace)

	def TO_MODE(self, inp):
		# This is a minilanguage keyword. Don't use it otherwise.
		self.mode = inp
		

class LED(Flip_Flop):
	def __init__(self, ui_obj):
		# This object takes a GTK_image
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
		# This object takes a GTK_label
		Register.__init__(self)
		self.note = ""
		self.disp = label_obj
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
			
	def update(self):
		self.disp.set_text(str(self.value))


class Bargraph(Register):
	def __init__(self, lamp_objs):
		# This object takes a list of GTK_image
		Register.__init__(self)
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
	def __init__(self, entry_obj):
		# This object takes a GTK_Entry
		Register.__init__(self)
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
	def __init__(self, label_obj, mode_indicator):
		# This object takes a GTK_entry
		Register.__init__(self)
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
		pattern = bin(A_BUS.get())[-2:]
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
	def __init__(self, button_objs):
		# This object takes a list of GTK_Buttons
		GPIO.__init__(self)
		self.timbre = "Piano"
	
	def set(self, inp=None):
		GPIO.set(self,inp)
		# Play note


## Weird ones:
class TackOn16:
	def __init__(self, msb, lsb, label_obj):
		self.msb = msb
		self.lsb = lsb
		self.disp = label_obj
		self.set()
		
	def set(self):

		val = join_byte(self.msb.get(), self.lsb.get())
		self.disp.set_text(str(val))


