# TODO: Test if the distinction between positive and negative flags works.

stt = {
"bool":		0b1000,
"great":	0b0100,
"equal":	0b0010,
"carry":	0b0001,
}

cond = {
"_":(0b000, 0b0, None),				# Always accept
":":(0b001, stt["carry"], 1),		# If there's an ALU carry
"+":(0b010, stt["bool"], 1),		# Bool is True
"-":(0b011, stt["bool"], 0),		# Bool is False
"!":(0b100, stt["equal"], 0),		# Different Numbers
"<":(0b101, stt["great"], 0),		# Lesser Number
">":(0b110, stt["great"], 1),		# Greater Number
"=":(0b111, stt["equal"], 1),		# Equal Numbers
}

opin = {
"nhalt":0b00000,"rhalt":0b00001,"chalt":0b00010, "ravn":0b00011, "poke":0b00100, "tell":0b00101,					# Exec
"ngoto":0b01000,"rgoto":0b01001,"cgoto":0b01010,"cont":0b01011,"gobak":0b01100,"rept":0b01101,						# Goto
"nmove":0b10000,"rmove":0b10001,"accfet":0b10010,"hexfet":0b10011,"utfet":0b10100, "xfeed":0b10101,					# Move
"!t":0b11000,"t>n":0b11001,"t>r":0b11010,"t>c":0b11011,"t+n":0b11100,"t+r":0b11101,"t+c":0b11110, "pwm":0b11111,	# time
}

class tree:
	child = dict()
	
	def __init__(self, **children):
		for each in children:
			self.child[each] = children[each]
	
	def isTree(self):
		return True
	
	def __getattr__(self, who):
		return self.child[who]

	def __setattr__(self,who,what):
		if type(self.child[who]) is tree:
			print("No overwriting nodes")
		else:
			self.child[who] = tree(**what)

ini = tree(
	skip =			0b00000001,
	read =			0b00000010,
	intsert =		0b00000100,
	auxput =		0b00001000,
	twoffer = tree(		
		cach_r =	0b00010000,
		ut_r =		0b00100000,
		acc_r =		0b00110000,
	),
	jump = tree( 
		cont =		0b01000000, 
		gobak =		0b10000000,
		rept =		0b11000000
	),
)
		
fin = tree(
	ut_ld =		0b00000001,
	ut_tg =		0b00000010,
	ut_go =		0b00000100,
	cach_w =	0b00001000,
	write =		0b00010000,
	slp_go =	0b00011000,
	jmp =		0b00100000,
	ravn =		0b01000000,
	pwm_go =	0b01100000,	
	xfeed =		0b10000000,
)
aux = tree(
	periphlag =		0b00000010,
	rfeed =			0b00000001,
)

opout = {
	# Exec
	"nhalt": 	(ini.intsert | ini.auxput, fin.slp_go, 0),
	"rhalt": 	(ini.read, fin.slp_go, 0),
	"chalt": 	(ini.twoffer.cach_r, fin.slp_go, 0),
	"ravn":		(ini.intsert | ini.auxput, fin.ravn | fin.ut_ld | fin.ut_go, 0),						# Sort of a HCF; Writes the address of every register to them by connecting the user timer to both the store and the write address bus.
	"poke":		(ini.read, 0, aux.periphlag),															# Simple signal to peripherial.
	"tell":		(ini.read | ini.auxput, 0, aux.periphlag),												# Send signal to peripherial to record a setup value. For example to set mode of a GPIO with external interface.
	# Goto
	"ngoto": 	(ini.intsert | ini.auxput, fin.jmp, 0),
	"rgoto": 	(ini.read, fin.jmp, 0),
	"cgoto": 	(ini.twoffer.cach_r, fin.jmp, 0),
	"cont": 	(ini.jump.cont | ini.intsert | ini.auxput , fin.jmp, 0),
	"gobak": 	(ini.jump.gobak | ini.intsert | ini.auxput , fin.jmp, 0),
	"rept": 	(ini.jump.rept | ini.intsert | ini.auxput , fin.jmp, 0),
	# Move
	"nmove": 	(ini.intsert, fin.write, 0),
	"rmove": 	(ini.read, fin.write, 0),
	"accfet": 	(ini.twoffer.acc_r, fin.cach_w, 0),
	"hexfet": 	(ini.intsert | ini.auxput, fin.cach_w, 0),
	"utfet": 	(ini.twoffer.ut_r, fin.cach_w, 0),
	"xfeed":	(ini.read, fin.xfeed, aux.rfeed),														# Swaps the value of a register with the accumulator.
	# Time
	"!t": 		(0,ini.ut_tg, 0),
	"t>n": 		(ini.intsert | ini.auxput, fin.ut_go | fin.ut_ld, 0),
	"t>r": 		(ini.read, fin.ut_go | fin.ut_ld, 0),
	"t>c": 		(ini.twoffer.cach_r, fin.ut_go | fin.ut_ld, 0),
	"t+n": 		(ini.intsert | ini.auxput, fin.ut_ld, 0),
	"t+r":	 	(ini.read, fin.ut_ld, 0),
	"t+c": 		(ini.twoffer.cach_r, fin.ut_ld, 0),
	"pwm":		(ini.intsert | ini.auxput, fin.pwm_go | fin.ut_go, 0),														# Generates a PWM signal by enabling a Flip-Flop that responds to the User Timer and resets it based on 2 comparators with two registers of the half period of each waveform swing.
}

skip = ini.skip

INIS = [skip] * 2**16
FINS = [skip] * 2**16
AUXS = [skip] * 2**16
DEBG = [bin(skip)] * 2**16

bogusSTT = [x for x in range(0b10000)]  # These bits might be in any either state and we don't care.

bunch = []

for bog in bogusSTT:
	bog = bin(bog)[2:].zfill(4)
	for s in range(max(stt.values())*2):
		for cmne, cnd in cond.items():
			st = bin(s)[2:].zfill(4)
			cn = bin(cnd[0])[2:].zfill(3)			
			if cnd[2] == 0:
				if cnd[1] ^ s == cnd[1]:
					bunch.append(bog+st+cn)
			if cnd[2] == 1:
				if cnd[1] & s == cnd[1]:
					bunch.append(bog+st+cn)
			else:  # if None
				bunch.append(bog+st+cn)

for possib in bunch:
	for mne, out in opout.items():
		inp = bin(opin[mne])[2:].zfill(5)
		addr = int(possib+inp,2)
		saddr = possib+inp
		INIS[addr] = out[0]
		FINS[addr] = out[1]
		AUXS[addr] = out[2]
		DEBG[addr] = saddr[0:4] +" | "+ saddr[4:8] +" | "+ saddr[8:11] +" | "+ saddr[11:17] +" : "+ bin(out[0])[2:].zfill(8)
		
with open("microcode/debug.txt", "w") as fl:
	fl.write("bogus | state | condit | opcode : ROM output\n\n")
	for each in DEBG:
		fl.write(each+"\n")


logisim = [[],[],[]]

logisim[0] = [hex(x)[2:].zfill(2) for x in INIS]
logisim[0] = [logisim[0][n:n+6] for n in range(0, len(logisim[0]), 6)]

logisim[1] = [hex(x)[2:].zfill(2) for x in FINS]
logisim[1] = [logisim[1][n:n+6] for n in range(0, len(logisim[1]), 6)]

logisim[2] = [hex(x)[2:].zfill(2) for x in AUXS]
logisim[2] = [logisim[2][n:n+6] for n in range(0, len(logisim[2]), 6)]

with open("microcode/initialCTRL.txt", "w") as fl:
	for group in logisim[0]:
#		fl.write("v2.0 raw")
		fl.write(" ".join(group)+"\n")
		
with open("microcode/finalCTRL.txt", "w") as fl:
	for group in logisim[1]:
#		fl.write("v2.0 raw")
		fl.write(" ".join(group)+"\n")
		
with open("microcode/auxCTRL.txt", "w") as fl:
	for group in logisim[2]:
#		fl.write("v2.0 raw")
		fl.write(" ".join(group)+"\n")

print("One day the this might print the ROM format of Logisim, but for now just copy and paste.")
print("Finished writing into «microcode/»")

