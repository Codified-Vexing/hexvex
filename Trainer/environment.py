#!/usr/bin/env python

__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

import time

import assembler as ass

class Environ:

	def __init__(self):
		
		# Get time when program starts
		self.START = int(time.time()*100000)
	
		# Get widget references
		#self.id = self.builder.get_object("id")
		self.mem = self.builder.get_object("prog_mem")
		self.reg_a = self.builder.get_object("reggae")
		self.reg_b = self.builder.get_object("reggie")
		self.reg_c = self.builder.get_object("barman")
		self.dipswt = self.builder.get_object("bouncer")
		self.blinker = self.builder.get_object("machine_heartbeat")
		
		# Instantiate HexVex and set which widgets show internal state.
		self.cpu = ass.Core(
							BLINKER=ass.LED(self.blinker),
							)

		# Setup output devices.
		self.cpu.add(ass.Num_Disp(self.reg_a), both_addr=0x0a)
		self.cpu.add(ass.Num_Disp(self.reg_b), both_addr=0x0b)
		self.cpu.add(ass.Bargraph(self.reg_c.get_children()), both_addr=0x0c)
		
		# Instantiate the devices
		dipswt = ass.DipSwitch(self.dipswt)
		
		# Connect input widgets to the HexVex device methods.
		self.dipswt.connect("activate", dipswt.intake)
	
		# Setup input devices
		self.cpu.add(dipswt, both_addr=0x0d)
		
	# Example signal handler:
	#def foo(self, widget, data=None):
	#	print("bar")

	def pause(self, widget):
		pass

	def execute(self, widget):
		start = self.mem.get_start_iter()
		end = self.mem.get_end_iter()
		PROG = self.mem.get_text(start, end, False)
		
		self.cpu(PROG)

if __name__ == "__main__":
	print("oopsies.")
else:
	pass
