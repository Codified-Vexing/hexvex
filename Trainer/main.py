#!/usr/bin/env python
"""
This is the emulator front-end. For now a testbed until we know how to make it 
work.
"""
__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

# TODO:
# Make more files imported into here so stuff is better organized. Eg. configs

import configuration as sett
from environment import Environ

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as g
from gi.repository import GObject as gob

class WindowMain (Environ):
	
	def __init__(self):
		# Get GUI from Glade file
		self.builder = g.Builder()
		self.builder.add_from_file("hxv_trainer.glade")  # UI file specified here
		
		# Display main window
		self.mainwin = self.builder.get_object("mainwin")  # The top-level window's ID could be "mainwin"
		#print(*dir(self.windowMain), sep="\n")
		self.mainwin.show()

		Environ.__init__(self)
		
		# A timed event. Can be used to make a looping function.
		# self.timer = GObject.timeout_add(self.milliseconds, self.method)
		
		# The thing that loops forever. Time in milliseconds.
		self.clkStepTime = None
		self.set_clkspeed()
		self.looptime = gob.timeout_add(200, self.looper)
		
		# Get the signals. After doing initial stuff to the UI, so that it doesn't trigger the callbacks.
		#self  <-- When you don't care. Just do the default stuff
		#{"signal": (callback, arg1, arg2, etc) , }  <-- each arg is whatever the signal emits when triggered, according to the docs.
		#{"signal": ((lambda widget: callback(widget, arg_a, arg_b, etc)) , }  <-- For custom callback arguments
		self.builder.connect_signals(self)
		
		#for pontual signal connections:
		#some_widget.connect("signal", self.callback)
		
		# Doffer
		self.mainwin.show_all()
		g.main()
	
	def metronome(self):
		# Pulse the HexVex clock
		next(self.cpu)
		return True  # Makes it loop again
	def looper(self):
		# Loop devices UI
		self.cpu.update()
		return True  # Makes it loop again
	
	def finish_it(self, widget=None, data=None):
		print("Quitting...")
		self.mainwin.destroy()
		g.main_quit()
		# Do «self.finish_it()» to exit by other means than pressing the window cross.
	
	def set_clkspeed(self, widget=None):
		if not widget is None:
			if type(widget) in (int, float):
				val = widget
			else:
				val = widget.get_value()
			#https://sciencing.com/exponential-equation-two-points-8117999.html
			val = sett.max_hz*val**(4)
			
			val = round(val, 3)
			sett.CLK = val
			
		self.freq_meter.set_text(str(sett.CLK))	
		if self.clkStepTime:
			gob.source_remove(self.clkStepTime)
	
		# The division by two is because the program pointers actually step
		# from 2 to 2 ticks so that the blinking LED has a moment off in between
		# steps, triggered by each real tick.
		self.clkStepTime = gob.timeout_add(int((1/sett.CLK*1000)/2), self.metronome)
		
	
	
if __name__ == "__main__":
	applic = WindowMain()
else:
	print("oopsies.")
