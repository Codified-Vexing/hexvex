# Version 0.86 - 14/2/2019
# License: Copyleft
# NOTICE: This assembler reads from type 1 assembly programs.
# This is the most basic assembler. No clever tricks and very straightforward mnemonic-to-hex conversion.º
# This version is altered to be used in the HexVex emulator.

from os.path import dirname

# TODO: Make the number wraping work
# TODO: Do something about the last byte of the instruction so it isn't just empty.
# TODO: Make it output to a file and not just display in terminal
# TODO: Actually write to a physical ROM
# TODO: Add a steganography option

prog_dir = "progs/"


n_trrp = 8  # Number of interrupts available.

cond_codes = {
	"_":0b000,  # Always
	":":0b001,  # Carry Detected
	"+":0b010,  # Bool True
	"-":0b011,  # Bool False
	"!":0b100,  # Different Numbers
	"<":0b101,  # Lesser-than Numbers
	">":0b110,  # Greater-than Numbers
	"=":0b111,  # Equal Numbers
}

op_codes = {
"nhalt":0b00000,"rhalt":0b00001,"chalt":0b00010, "ravn":0b00011,													# Exec
"ngoto":0b01000,"rgoto":0b01001,"cgoto":0b01010,"cont":0b01011,"gobak":0b01100,"rept":0b01101,						# Goto
"nmove":0b10000,"rmove":0b10001,"accfet":0b10010,"hexfet":0b10011,"utfet":0b10100, "xfeed":0b10101,					# Move
"!t":0b11000,"t>n":0b11001,"t>r":0b11010,"t>c":0b11011,"t+n":0b11100,"t+r":0b11101,"t+c":0b11110, "pwm":0b11111,	# time
}

# For modelling in Falstad's Circuit sim
inps = ["a"+str(i) for i in range(16)]
outs = ["q"+str(i) for i in range(8)]

pointer = 0 # Current line being interpreted.
uvars = {}  # Variables
subrs = {}  # Subroutine pointers
fakeROM = {}  # For debug purposes. Or is it?!

process = []


def wrapn(n, maxi):
	# The algorithm for this is WIP
	return n % maxi

# Pre-Processing!
def importer(url):
	global pointer
	with open(url, "r") as fl:
		for li in fl:
			li = li[:li.find("#")].strip()
			if li:
				if li[0] == "|":  # It's an import
					importer(dirname(prog_dir)+"/"+li[1:])
				elif li[0] == "*":  # It's a variable
					part = li.split("=")
					uvars[part[0][1:].strip()] = part[1].strip()
				elif li[0] =="[" and li[-1] == "]":  # It's a goto label
						subrs[li[1:-1]] = pointer
				else:
					pointer += 4
					process.append(li)
asmfile = input("Which xasm file? programs/")
if len(asmfile) >= 2:
	prog_dir += asmfile
else:
	prog_dir += "fibonacci.xasm"
importer(prog_dir)

print("\n---VARS---")
for var, val in uvars.items():
	print(var, "=", val)
print("\n---POINTERS---")
for var, val in subrs.items():
	print(var, "=", val)
	if var[:-1] == "trrp":
		point = int(var[-1:])*4+3
		point = point ^ (2**16-1)
		place = bin(val)[2:].zfill(16)
		print(place)
		cond = cond_codes["_"]
		opcode = op_codes["ngoto"]
		ctrl = int(bin(cond)[2:].zfill(3)+bin(opcode)[2:].zfill(5),2)
		fakeROM[point] = ctrl
		fakeROM[point+1] = int(place[8:],2)
		fakeROM[point+2] = int(place[:8],2)
		fakeROM[point+3] = 0

# Making the vars proper integers:
for var,val in uvars.items():
	uvars[var]  = eval(val)

# Actual processing.
pointer = 0
for li in process:
	byte = li.split(" ")

	cond = cond_codes[byte[0][0]]
	opcode = op_codes[byte[0][1:]]
	ctrl = int(bin(cond)[2:].zfill(3)+bin(opcode)[2:].zfill(5),2)
	
	if len(byte) == 1:
		arga = 0
		argb = 0
	elif len(byte) == 3:
		arga = byte[1]
		if arga in uvars:
			arga = uvars[arga]		
		
		arga = eval(str(arga))
					
		argb = byte[2]
		if argb in uvars:
			argb = uvars[argb]
			
		argb = eval(str(argb))
			
		# If the numbers don't fit in a byte, then wrap them around
		arga = wrapn(arga, ((2**8)/2))
		argb = wrapn(argb, ((2**8)/2))

	elif len(byte) == 2:
		hexa = byte[1]
		if hexa in uvars:
			hexa = uvars[hexa]
		elif hexa in subrs:
			hexa = subrs[hexa]
		
		hexa = eval(str(hexa))
		
		if hexa >= 2**8:
			# If the numbers don't fit in a hex, then wrap them around
			hexa = bin(wrapn(hexa, (2**16/2)))[2:].zfill(16)
			
			argb = int(hexa[:8],2)
			arga = int(hexa[8:],2)
			# argb and arga may seem swapped, but it must be accounted the first-in-first-out mechanism of loading bytes from the ROM.
		else:
			arga = wrapn(hexa, (2**8/2))
			argb = 0
	
	# Make 2s complements
	if arga < 0:
		arga = ~arga+1
	if argb < 0:
		argb = ~argb+1
	
	fakeROM[pointer] = ctrl
	pointer += 1
	fakeROM[pointer] = arga
	pointer += 1
	fakeROM[pointer] = argb
	pointer += 1
	fakeROM[pointer] = 0
	pointer += 1
	
		
print("\n---PROG---")
print(*process, sep="\n")



