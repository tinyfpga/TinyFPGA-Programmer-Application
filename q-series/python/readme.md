Programming Quickfeather boards with TinyFPGA-Programmer-Application

The tinyfpga-programmer-gui.py can run in either GUI mode or CLI mode.  GUI mode only works well on systems
that report USB VID and PID, because the GUI uses that information to determine which serial ports are connected
to quickfeather boards. CLI mode allows you to specify which port to use, and thus works even when the system does not
report USB VID and PID.  This document focuses on CLI mode.

Help is available by running with the --help parameter:

* $ python3 tinyfpga-programmer-gui --help

The TinyFPGA programmer has a flash memory map for 5 bin files, and corresponding CRC for each of them.
The 5 bin files are:
  * bootloader
  * bootfpga
  * m4app
  * appfpga (for future use)
  * appffe (for future use)
  
The bootloader is loaded by a reset.  It handles either communicating with the TinyFPGA-Programmer to load new bin files into the flash,
or it loads m4 app binary and transfers control to it.  The bootfpga area contains the binary for the fpga image that the bootlaoder uses.
The m4 app image is expected to contain and load any fpga image that it requires.

The flash memory map defined for q-series devices is:

|Item	        |Status	|Start	    |Size	    |End		        |Start	    |Size	    |End|
|-----          |-------|----------:|----------:|------------------:|----------:|----------:|--:|
|bootloader	    |Used	|0x0000_0000|0x0001_0000|0x0000_FFFF		|-   	     |65,536 	|65,536 |
|bootfpga CRC	|Used	|0x0001_0000|          8|	0x0001_0007		|65,536 	 |8 	  |65,544| 
|appfpga CRC	|Future	|0x0001_1000|	          8|	0x0001_1007	|	 69,632 |	      8 |	  69,640 
appffe CRC	    |Future	|0x0001_2000|	          8|	0x0001_2007	|	 73,728 |	      8 |	  73,736 
M4app CRC	    |Used	|0x0001_3000|	          8|	0x0001_3007	|	 77,824 |	      8 |	  77,832 
bootloader CRC	|Used	|0x0001_4000|	          8|	0x0001_4007	|	 81,920 |	      8 |	  81,928 
bootfpga	    |Used	|0x0002_0000|	0x0002_0000|	0x0003_FFFF	|	 131,072 |	 131,072 |	 262,144 
appfpga	        |Future	|0x0004_0000|	0x0002_0000|	0x0005_FFFF	|	 262,144 |	 131,072 |	 393,216 
appffe	        |Future	|0x0006_0000|	0x0002_0000|	0x0007_FFFF	|	 393,216 |	 131,072 |	 524,288 
M4app	        |Used	|0x0008_0000|	0x0006_E000|	0x000E_DFFF	|	 524,288 |	 450,560 |	 974,848 

