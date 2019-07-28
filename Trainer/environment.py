#!/usr/bin/env python

__author__ = "Diogo JC Duarte"
__version__ = "0.1.0"
__license__ = "GNU GPL-3.0"

import time
import configuration as sett
import assembler as ass
import hxv_wiring as H

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as g

class Environ:

	def __init__(self):
		
		# Get time when program starts
		self.START = int(time.time()*100000)
			
		

		# Get widget references
		#self.id = self.builder.get_object("id")
		self.main_pane = self.builder.get_object("main_pane")
		self.aluLt = self.builder.get_object("alu_list")
		self.devcLt = self.builder.get_object("device_list")
		self.devc_kind = self.builder.get_object("device_picker")
		self.fileLt = self.builder.get_object("file_list")
		self.mem = self.builder.get_object("assm_area")
		self.clkstp = self.builder.get_object("freeze_butt")
		self.freq_meter = self.builder.get_object("hertz_disp")
		self.stt_cell = self.builder.get_object("State_Cell")
		self.intern_cell = self.builder.get_object("internals_frame")
		
		# Instantiate Virtual Hardware devices.
		W = H.Wares()
		# Instantiate HexVex and set which widgets show internal state.
		self.cpu = ass.Core( internals = W,
							BLINKER=H.LED(W, obj=self.builder.get_object("machine_heartbeat")),
							RAVN=H.LED(W, obj=self.builder.get_object("ravn")),
							WAIT=H.LED(W, obj=self.builder.get_object("wait")),
							BOOL=H.LED(W, obj=self.builder.get_object("bool")),
							GRTR=H.LED(W, obj=self.builder.get_object("grtr")),
							EQAL=H.LED(W, obj=self.builder.get_object("eqal")),
							CRRY=H.LED(W, obj=self.builder.get_object("crry")),
							PWM=H.LED(W, obj=self.builder.get_object("pwm")),
							acc_lsb=H.Bargraph(W, obj=self.builder.get_object("acc_lsb").get_children()),
							acc_msb=H.Bargraph(W, obj=self.builder.get_object("acc_msb").get_children()),
							cach_lsb=H.Bargraph(W, obj=self.builder.get_object("cache_lsb").get_children()),
							cach_msb=H.Bargraph(W, obj=self.builder.get_object("cache_msb").get_children()),
							utmr_lsb=H.Bargraph(W, obj=self.builder.get_object("utmr_lsb").get_children()),
							utmr_msb=H.Bargraph(W, obj=self.builder.get_object("utmr_msb").get_children()),
							stmr_lsb=H.Bargraph(W, obj=self.builder.get_object("stmr_lsb").get_children()),
							stmr_msb=H.Bargraph(W, obj=self.builder.get_object("stmr_msb").get_children()),
							)
		# Mirror widgets copy the value of existing devices, so you can
		# display the same state on different widgets.
		mirrors = (
					(W.acc_msb, W.acc_lsb, self.builder.get_object("acc_num")),
					(W.cach_msb, W.cach_lsb, self.builder.get_object("cache_num")),
					(W.utmr_msb, W.utmr_lsb, self.builder.get_object("utmr_num")),
					(W.stmr_msb, W.stmr_lsb, self.builder.get_object("stmr_num")),
					)
		for each in mirrors:			
			m, l, widget = each
			tacked = H.TackOnSTT(m, l, widget)
			m.mirrors.append(tacked)
			l.mirrors.append(tacked)
					
		#Instantiate and setup peripherals		
		# read address, write address, device kind, initial value, comment
		for each in sett.default_peripherals:
			read, write, kind, args = each			
			self.new_device(kind, read, write, args)
		
		# Instantiate and Setup the ALU modules
		for addr, each in sett.default_alu.items():
			name, logos = each
			inst = H.ALU(W, name, logos)
			self.cpu.add(inst, write_addr=addr)
			self.aluLt.add(inst.get_ui())


	def new_device(self, kind, read, write, args):
		funk = getattr(H, kind)(self.cpu.I, **args)
		form = funk.get_ui(read, write)
		if read:
			self.cpu.add(funk, read_addr=read)
		if write:
			self.cpu.add(funk, write_addr=write)
		
		self.devcLt.pack_start(form,0,1,0)
		form.show_all()

		
	# Example signal handler:
	#def foo(self, widget, data=None):
	#	print("bar")
	def execute(self, widget):
		start = self.mem.get_start_iter()
		end = self.mem.get_end_iter()
		raw_program = self.mem.get_text(start, end, False)
		
		self.cpu(raw_program)
		
		self.clkstp.set_active(False)
		if sett.save_with_exec:
			self.save_prog()
		

	def load_file(self, *foo, flnm=None):
		if flnm:
			url = flnm
		else:
			url = self.fileLt.get_active_text()
			if url in self.fetch_files.keys():
				url = self.fetch_files[url]
			else:
				return False
		with open(url) as fl:
			prog = fl.read()
		self.mem.set_text(prog)
		self.clkstp.set_active(True)
		return True
		
	def smart_load(self, widget):
		name = self.fileLt.get_active_text()
		if not name[-5:] == ".xasm":
			url = name+".xasm"
			name = name.title()
		else:
			url = name
			name = name[:-5].title()
		if len(name) >= 3:
			if not self.load_file(sett.prog_dir+url):
				self.load_file(flnm="template")
				widget.set_text(name)
				self.fetch_files[name] = sett.prog_dir+url
				san_id = "_".join(name.lower().split(" "))
				self.fileLt.prepend(san_id,name)
	
	def save_prog(self, *foo):
		start = self.mem.get_start_iter()
		end = self.mem.get_end_iter()
		raw_program = self.mem.get_text(start, end, False)

		with open(self.fetch_files[self.fileLt.get_active_text()], "w") as fl:
			fl.write(raw_program)
			
	def hide_internals(self, widget):
		pick = ("show", "hide")
		getattr(self.intern_cell, pick[widget.get_active()])()
	def hide_state(self, widget):
		pick = ("show", "hide")
		getattr(self.stt_cell, pick[widget.get_active()])()
	
	def add_peripheral(self, widget):
		aliases = {
				"GPIO": "GPIO",
				"Number Display": "Num_Disp",
				"Binary Display": "Bargraph",
				"Generic Input": "DipSwitch",
				"Timepiece": "RTC",
				}
		kind = aliases.get(self.devc_kind.get_active_text(),"GPIO")
		self.new_device(kind, None, None, tuple())
	
	def add_comment(self, widget):
		comment = g.TextView()
		#Make wrap
		#Add right and left margin
		#Make easier to see
		self.devcLt.pack_start(comment,0,1,6)
		comment.show()

if __name__ == "__main__":
	print("oopsies.")
else:
	pass
