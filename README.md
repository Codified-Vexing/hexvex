# hexvex
Any software related to my computer/microcontroller arquitecture project go here. This device's hardware has never been built to date and so this is an hypothetical project with a real software backbone.
All the main files here can be found in my website [VexDex.eu](https://www.vexdex.eu) in a less formal form along with an article describing the project. And probably outdated form, if this repository happens to have many contributions.

The «HexVex.png» file is the full diagram of the HexVex hardware in logic block form. It's useful as a reference to understand how the assembler and microcode act together with the hardware.

«DOCUMENTATION.odt» is the reference manual for the HexVex assembly code along with other information on the project in a stand-alone form, meaning that if all you get is that document, you can understand and use the project without knowing about this repository or vexdex.eu articles.

Inside «Low_Level_Scripts» there's the following:
- «hxv_assm_t1.py» is the assembler. It takes programs in human-readable assembly format (I call ".xasm") and output binaries to be loaded into HexVex's program memory. It can also output in other formats, for debugging and for kicks.
- «hxv_microcode_builder.py» generates binaries to be stored in a HexVex decoder ROMs

These are bound to become obsolete after the Trainer works, as it will have its own version of assembly code parser.

The «programs» folder has example assembly code scripts to aid someone learning the language.

«Trainer» pertains to an emulator written in Python with GTK3+ which is in development. It will allow to test and demonstrate HexVex code without requiring a simulation of the circuitry or to build actual hardware.
For now, there's a testbed with a back-end nearing the actual Trainer as designed. A more proper UI will become available when made to integrate with the back-end.

## TO DO:
- The Documentation has most of the important things, but it's still incomplete and doesn't look good the further down in the pages you read. This ought to be fixed after the next big improvement to the project software.
- The Assembler and Microcode builders need a feature to write into physical ROMs or SRAMs. Probably using an arduino. That's how Ben Eater did it.
- Probably is a good idea to unify the interface of the Assembler and Builder. Maybe the Trainer can be the facility for this and the current scripts will be left as independent CLI and suckless interfaces for low level use.
