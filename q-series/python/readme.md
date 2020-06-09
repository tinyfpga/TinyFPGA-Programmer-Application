# Programming Quickfeather boards

## Installation


## Programming
The tinyfpga-programmer-gui.py can run in either GUI mode or CLI mode.  GUI mode only works well on systems
that report USB VID and PID, because the GUI uses that information to determine which serial ports are connected
to quickfeather boards. CLI mode allows you to specify which port to use, and thus works even when the system does not
report USB VID and PID.  This document focuses on CLI mode.

Help is available by running with the --help parameter:

```sh
python3 tinyfpga-programmer-gui --help
```
This will result in:
```
usage: tinyfpga-programmer-gui.py [-h] [--m4app app.bin]
                                  [--bootloader boot.bin]
                                  [--bootfpga fpga.bin] [--reset]
                                  [--port /dev/ttySx] [--crc] [--checkrev]
                                  [--update] [--mfgpkg qf_mfgpkg/]

optional arguments:
  -h, --help            show this help message and exit
  --m4app app.bin       m4 application program
  --bootloader boot.bin, --bl boot.bin
                        m4 bootloader program WARNING: do you really need to
                        do this? It is not common, and getting it wrong can
                        make you device non-functional
  --bootfpga fpga.bin   FPGA image to be used during programming WARNING: do
                        you really need to do this? It is not common, and
                        getting it wrong can make you device non-functional
  --reset               reset attached device
  --port /dev/ttySx     use this port
  --crc                 print CRCs
  --checkrev            check if CRC matches (flash is up-to-date)
  --update              program flash only if CRC mismatch (not up-to-date)
  --mfgpkg qf_mfgpkg/   directory containing all necessary binaries
  ```
The programmer allows you to specify the port using the *--port port-name* option.  The form of *port-name* varies depending on the system: COM## on PC/Windows, /dev/ttyS## on PC/wsl2/Ubuntu18, /dev/ttyACM# on PC/Ubuntu18.


## Flash memory map
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

