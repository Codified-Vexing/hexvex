# hexvex
Any software related to my computer/microcontroller arquitecture project go here. This device's hardware has never been built to date and so this is an hypothetical project with a real software backbone.
All the main files here can be found in my website [VexDex.eu](https://www.vexdex.eu) in a less formal form along with an article describing the project. And probably outdated form, if this repository happens to have many contributions.

The «HexVex.png» file is the full diagram of the HexVex hardware in logic block form. It's useful as a reference to understand how the assembler and microcode act together with the hardware.

«DOCUMENTATION.odt» is the reference manual for the HexVex assembly code along with other information on the project in a stand-alone form, meaning that if all you get is that document, you can understand and use the project without knowing about this repository or vexdex.eu articles.

«hxv_assm_t1.py» is the assembler. It takes programs in human-readable assembly format (I call ".xasm") and output binaries to be loaded into HexVex's program memory. It can also output in other formats, for debugging and for kicks.

«hxv_microcode_builder.py» generates binaries to be stored in a HexVex decoder ROMs
