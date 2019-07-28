#!/usr/bin/env python
"""
Here lies all the classes out of which peripheral devices are defined by.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

import datetime

from some_functions import *
import some_functions as some  # So the namespace can be referred to by the ALU class.
import configuration as sett
	
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as g
	
## Device primitives:

class Flip_Flop:
	def __init__(self, core, init=False):
		self.c = core
		self.value = init
		
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
	def __ini__(self, core, init=False, bit_of_interest=0):
		Flip_Flop.__init__(self, core, init)
		self.boi=bit_of_interest
		
	def set(self, val=None):
		if val is None:
			val = self.c.M_BUS.get()
			val = bin(val)[:1:-1]
			val = bool(val[self.boi])
		Flip_Flop.set(self, val)
		
class Register:
	def __init__(self, core, init=0):
		self.c = core
		self.value = init
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
	def __init__(self, core, note="Bogus ALU module", logic="TO_ACCUM({0})##SETUP LOGIC="):
		self.c = core
		self.note = note
		
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
		
	def get_ui(self):
		container = g.Box(0,0)
		note_area = g.Label(self.note)
		addr_area = g.Label("????")
		container.pack_start(addr_area, 0, 1, 6)
		container.pack_start(note_area, 1, 1, 6)
		container.pack_end(g.Button.new_with_label("Delete"), 0, 1, 6)
		return container
		
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
		self.c.I_BUS_set(wrap(inp, 0x10000))

	def TO_FLAGS(self, pattern, mode):
		pick = ("set", "toggle")
		nam = ["BOOL", "EQAL", "GRTR", "CRRY"]
		flag = [self.c.BOOL, self.c.EQAL, self.c.GRTR, self.c.CRRY]
		for which, state in enumerate(pattern):
			if state != "x":
				getattr(flag[which], pick[mode])(bool(int(state,2)))

class LED(Flip_Flop):
	def __init__(self, core, init=False, obj=None):
		Flip_Flop.__init__(self, core, init)
		self.pick = ("gtk-media-stop", "gtk-media-record")
		
		if obj is None:
			self.do = g.Image.new_from_icon_name(self.pick[init], 4)
		else:
			self.do = obj

	def get_ui(self):
		return self.do

	def set(self, val=True):
		Flip_Flop.set(self, val)
		self.update()
	
	def update(self):
		self.do.set_from_stock(self.pick[int(self.value)], 4)

class Num_Disp(Register):
	def __init__(self, core, init=0, note="", obj=None):
		Register.__init__(self, core, init)
		self.note = note
		
		if obj is None:
			self.disp = g.label(init)
		else:
			self.disp = obj
	
	def get_ui(self):
		return self.disp()
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()
			
	def update(self):
		val = str(self.value)
		self.disp.set_text(val)


class Bargraph(Register):
	def __init__(self, core, init=0, note="", obj=None):
		Register.__init__(self, core, init)
		self.pick = ("gtk-media-stop", "gtk-media-record")
		self.note = note
		
		if obj is None:
			self.bar = list()
			b = bin(self.value)[2:].zfill(8)
			for led in b:
				self.bar.append( g.Image.new_from_icon_name(self.pick[int(led)], 4) )
		else:
			self.bar = obj

	def get_ui(self, read, write):
		container = g.Box(0,0)
		note_area = g.Entry()
		note_area.set_text(self.note)
		read_area = g.Entry()
		read_area.set_text(str(read))
		read_area.set_max_length(6)
		read_area.set_max_width_chars(6)
		read_area.set_width_chars(6)
		read_area.set_sensitive(False)
		write_area = g.Entry()
		write_area.set_text(str(write))
		write_area.set_max_length(6)
		write_area.set_max_width_chars(6)
		write_area.set_width_chars(6)
		container.pack_start(read_area, 0, 1, 6)
		container.pack_start(write_area, 0, 1, 6)
		for each in self.bar:
			container.pack_start(each, 0, 1, 3)
		container.pack_start(note_area, 1, 1, 6)
		container.pack_end(g.Button.new_with_label("Delete"), 0, 1, 6)
		return container

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
	def __init__(self, core, init=0, note="", obj=None):
		# This object takes a GTK_Entry
		Register.__init__(self, core, init)
		self.note = note
		
		if obj is None:
			self.entry = g.Entry()
			self.entry.set_text(init)
		else:
			self.entry = entry_obj
		
		entry_obj.connect("activate", self.intake)
	
	def get_ui(self):
		return self.entry
	
	def set(self, inp=None):
		Register.set(self,inp)
		self.update()

	def update(self):
		self.entry.set_text(str(self.value))
	
	def intake(self, widget, signal):
		inp = int(widget.get_text())
		self.set(inp)
		
	
class GPIO(Register):
	def __init__(self, core, init=0, note="", obj=None):
		# obj = g.Entry, g.Image
		Register.__init__(self, core, init)
		self.pick = (("gtk-fullscreen", "gtk-leave-fullscreen"), ("This is a Written-to device", "This is a Readable device"))
		self.note = note
		self.mode = False  # False = Readable device; True = Written-to device
		
		if obj is None:
			self.disp, self.LED = g.Entry(), g.Image.new_from_icon_name(self.pick[0][init], 5)
			self.disp.set_text(str(init))
			self.LED.set_tooltip_text(self.pick[1][int(self.mode)])
		else:
			self.disp, self.LED = obj
		
		self.disp.connect("activate", self.intake)
	
	def get_ui(self, read, write):
		container = g.Box(0,0)
		note_area = g.Entry()
		note_area.set_text(self.note)
		read_area = g.Entry()
		read_area.set_text(str(read))
		read_area.set_max_length(6)
		read_area.set_max_width_chars(6)
		read_area.set_width_chars(6)
		write_area = g.Entry()
		write_area.set_text(str(write))
		write_area.set_max_length(6)
		write_area.set_max_width_chars(6)
		write_area.set_width_chars(6)
		self.disp.set_max_length(6)
		self.disp.set_max_width_chars(6)
		self.disp.set_width_chars(6)
		container.pack_start(read_area, 0, 1, 6)
		container.pack_start(write_area, 0, 1, 6)
		container.pack_start(self.disp, 0, 1, 6)
		container.pack_start(self.LED, 0, 1, 6)
		container.pack_start(note_area, 1, 1, 6)
		container.pack_end(g.Button.new_with_label("Delete"), 0, 1, 6)
		return container
		
	
	def set(self, inp=None):
		if not self.mode:
			# When "None", some non-user system is forcing the value.
			Register.set(self,inp)
		self.update()
	
	def setup(self):
		pattern = bin(self.c.A_BUS.get())[2:].zfill(8)[-2:]
		pick = {"00":self.mode, "01":not self.mode, "10":False, "11": True}
		self.mode = pick[pattern]
		self.update()
	
	def update(self):
		self.disp.set_text(str(self.value))
		self.LED.set_from_stock(self.pick[0][int(self.mode)], 5)
		self.LED.set_tooltip_text(self.pick[1][int(self.mode)])

	def intake(self, widget):
		if not self.mode:
			inp = int(widget.get_text(), 0)
			self.set(inp)
		else:
			widget.set_text(self.get())

class Keyboard(GPIO):
	"""
	A musical sequencing device.
	The user can press keys to play sound and input a number or have the 
	program send the same number to make it play automatically.
	That number is associated with a note/frequency. The mode can be set to
	pick the musical instrument, or voice.
	On the user interface, the device can be muted.
	"""
	def __init__(self, core, init=0, obj=None):
		# This object takes a list of GTK_Buttons
		GPIO.__init__(self, core, 0)
		self.timbre = ("Piano", "Guitar", "Harmonica", "Drum", "High_Hat")
	
	def set(self, inp=None):
		GPIO.set(self,inp)
		# Play note


class RTC(Register):
	"""
	This is a real-time clock. It can only be read and will tell the current
	time by supplying the number of the hour, minute, second, or combination, 
	depending on the mode.
	The year is in the last 2 digits format.
	And offset and hour format can be adjusted through UI. Default is 24Hr UTC
	"""
	def __init__(self, core, init=0, note=""):
		Register.__init__(self, core, datetime.datetime.utcnow().year)
		self.note = note
		self.mode = 1  # millenium, year, month, week, day, hour, minute, second
		self.offset = 0

	def get_ui(self, read, write):
		container = g.Box(0,0)
		note_area = g.Entry()
		note_area.set_text(self.note)
		read_area = g.Entry()
		read_area.set_text(str(read))
		read_area.set_max_length(6)
		read_area.set_max_width_chars(6)
		read_area.set_width_chars(6)
		read_area.set_sensitive(False)
		write_area = g.Entry()
		write_area.set_text(str(write))
		write_area.set_max_length(6)
		write_area.set_max_width_chars(6)
		write_area.set_width_chars(6)
		year=g.SpinButton.new(g.Adjustment(0, -100, 101, 1, 1, 1), 1.5, 0)
		month=g.SpinButton.new(g.Adjustment(0, -12, 13, 1, 3, 1), 1.5, 0)
		day=g.SpinButton.new(g.Adjustment(0, -31, 32, 1, 7, 1), 1.5, 0)
		hour=g.SpinButton.new(g.Adjustment(0, -24, 25, 1, 6, 1), 1.5, 0)
		minute=g.SpinButton.new(g.Adjustment(0, -60, 61, 1, 15, 1), 1.5, 0)
		second=g.SpinButton.new(g.Adjustment(0, -60, 61, 1, 15, 1), 1.5, 0)
		row1 = g.Box(0,0)
		row1.pack_start(year, 0, 1, 0)
		row1.pack_start(month, 0, 1, 0)
		row1.pack_start(day, 0, 1, 0)
		row2 = g.Box(0,0)
		row2.pack_start(hour, 0, 1, 0)
		row2.pack_start(minute, 0, 1, 0)
		row2.pack_start(second, 0, 1, 0)
		ctrl = g.Box(1,0)
		ctrl.pack_start(row1, 0, 1, 0)
		ctrl.pack_start(row2, 0, 1, 0)
		container.pack_start(read_area, 0, 1, 6)
		container.pack_start(write_area, 0, 1, 6)
		container.pack_start(g.Label("+OFFSET:"), 0, 1, 6)
		container.pack_start(ctrl, 0, 1, 0)
		container.pack_start(note_area, 1, 1, 0)
		container.pack_end(g.Button.new_with_label("Delete"), 0, 1, 6)
		return container

	def set(self,inp=None):
		pass
	def get(self):
		now = datetime.datetime.utcnow()
		pick = [
				now.second,
				now.minute,
				now.hour,
				now.day,
				now.month,
				now.year[-2:],
				now.year[1],
				]
		self.value = pick[self.mode]
		for k, each in enumerate(self.value):
			self.value[k] += self.offset[k]
		return getattr(now, self.value)
	def setup(self):
		num = bin(self.c.A_BUS.get())
		self.mode = wrap(num, 8)

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


