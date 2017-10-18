#!python2.7
import sys
import os

# need to find the correct location for bundled packages
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, 'pkgs'))
sys.path.insert(0, os.path.join(script_path, 'a-series-programmer', 'python'))
sys.path.insert(0, os.path.join(script_path, 'b-series', 'programmer'))

import serial
import array
import time
#from intelhex import IntelHex
from Tkinter import *
from ttk import *
import tkFileDialog
import threading
import os
import os.path
import traceback
from serial.tools.list_ports import comports

from tinyfpgab import h, TinyFPGAB
import tinyfpgaa

########################################
## Programmer Hardware Adapters
########################################
class ProgrammerHardwareAdapter(object):
    def __init__(self, port):
        self.port = port
        #self.bus, self.portnum = [int(x) for x in self.port[2].split('=')[-1].split('-')]

    @staticmethod
    def canProgram(port):
        pass

    def displayName(self):
        pass

    def checkPortStatus(self):
        pass

    def exitBootloader(self):
        pass

    def reset(self):
        # TODO: for now...let's not bother with resetting the port
        pass
        #try:
        #    import usb
        #    device = usb.core.find(custom_match = lambda d: d.bus == self.bus and d.port_number == self.portnum)
        #    device.reset()
        #except:
        #    traceback.print_exc()


class TinyFPGABSeries(ProgrammerHardwareAdapter):
    def __init__(self, port):
        super(TinyFPGABSeries, self).__init__(port)

    @staticmethod
    def canProgram(port):
        return "1209:2100" in port[2] or "0000:0000" in port[2]

    def displayName(self):
        if "1209:2100" in self.port[2]:
            return "%s (TinyFPGA Bx)" % self.port[0]

        if "0000:0000" in self.port[2]:
            return "%s (Maybe TinyFPGA Bx Prototype)" % self.port[0]

    def get_file_extensions(self):
        return ('.hex', '.bin')

    def program(self, filename, progress):
        global max_progress

        with serial.Serial(self.port[0], 115200, timeout=2, writeTimeout=2) as ser:
            fpga = TinyFPGAB(ser, progress)

            (addr, bitstream) = fpga.slurp(filename)

            max_progress = len(bitstream) * 3 

            try:
                fpga.program_bitstream(addr, bitstream)
            except:
                program_failure = True
                traceback.print_exc()



    def checkPortStatus(self, update_button_state):
        try:
            with serial.Serial(self.port[0], 115200, timeout=0.2, writeTimeout=0.2) as ser:
                fpga = TinyFPGAB(ser)
            
                if fpga.is_bootloader_active():
                    com_port_status_sv.set("Connected to TinyFPGA B2. Ready to program.")
                    return True
                else:            
                    com_port_status_sv.set("Unable to communicate with TinyFPGA. Reconnect and reset TinyFPGA before programming.")
                    return False

        except serial.SerialTimeoutException:
            com_port_status_sv.set("Hmm...try pressing the reset button on TinyFPGA again.")
            return False

        except:
            com_port_status_sv.set("Bootloader not active. Press reset button on TinyFPGA before programming.")
            return False

    def exitBootloader(self):
        with serial.Serial(self.port[0], 10000000, timeout=0.2, writeTimeout=0.2) as ser:
            try:
                TinyFPGAB(ser).boot()

            except serial.SerialTimeoutException:
                com_port_status_sv.set("Hmm...try pressing the reset button on TinyFPGA again.")
            
        

class TinyFPGAASeries(ProgrammerHardwareAdapter):
    def __init__(self, port):
        super(TinyFPGAASeries, self).__init__(port)

    @staticmethod
    def canProgram(port):
        return "1209:2101" in port[2]

    def displayName(self):
        return "%s (TinyFPGA Ax)" % self.port[0]

    def get_file_extensions(self):
        return ('.jed')

    def program(self, filename, progress):
        global max_progress

        with serial.Serial(self.port[0], 12000000, timeout=10, writeTimeout=5) as ser:            
            async_serial = tinyfpgaa.SyncSerial(ser)
            pins = tinyfpgaa.JtagTinyFpgaProgrammer(async_serial)
            jtag = tinyfpgaa.Jtag(pins)
            programmer = tinyfpgaa.JtagCustomProgrammer(jtag)
           
            progress("Parsing JEDEC file")
            jedec_file = tinyfpgaa.JedecFile(open(filename, 'r'))

            max_progress = jedec_file.numRows() * 3

            try:
                programmer.program(jedec_file, progress)

            except:
                program_failure = True
                self.reset()
                traceback.print_exc()

    port_success = False
    def checkPortStatus(self, update_button_state):
        global port_success
        with serial.Serial(self.port[0], 12000000, timeout=.5, writeTimeout=0.1) as ser:
            async_serial = tinyfpgaa.SyncSerial(ser)
            pins = tinyfpgaa.JtagTinyFpgaProgrammer(async_serial)
            jtag = tinyfpgaa.Jtag(pins)
            programmer = tinyfpgaa.JtagCustomProgrammer(jtag)
            port_success = False

            def status_callback(status):
                global port_success
                
                if status == [0x43, 0x80, 0x2B, 0x01]:
                    com_port_status_sv.set("Connected to TinyFPGA A1. Ready to program.")
                    port_success = True

                elif status == [0x43, 0xA0, 0x2B, 0x01]:
                    com_port_status_sv.set("Connected to TinyFPGA A2. Ready to program.")
                    port_success = True

                else:
                    com_port_status_sv.set("Cannot identify FPGA.  Please ensure proper FPGA power and JTAG connection.")
                    port_success = False

            ### read idcode
            programmer.write_ir(8, 0xE0)
            programmer.read_dr(32, status_callback, blocking = True)
            return port_success

    def exitBootloader(self):
        pass


        
        



################################################################################
################################################################################
##
## TinyFPGA Programmer GUI
##
################################################################################
################################################################################

communication_lock = threading.Lock()

r = Tk()
r.title("TinyFPGA Programmer")
r.resizable(width=False, height=False)

program_in_progress = False
program_failure = False

program_fpga_b = Button(r, text="Program FPGA")
program_progress_pb = Progressbar(r, orient="horizontal", length=400, mode="determinate")

boot_fpga_b = Button(r, text="Exit Bootloader")

program_status_sv = StringVar(r)

serial_port_ready = False
bitstream_file_ready = False
file_mtime = 0

def update_button_state(new_serial_port_ready = None):
    global serial_port_ready
    global bitstream_file_ready

    if new_serial_port_ready is not None:
        serial_port_ready = new_serial_port_ready

    if serial_port_ready and not program_in_progress:
        boot_fpga_b.config(state=NORMAL)

        if bitstream_file_ready:
            program_fpga_b.config(state=NORMAL)
        else:
            program_fpga_b.config(state=DISABLED)

    else:
        boot_fpga_b.config(state=DISABLED)
        program_fpga_b.config(state=DISABLED)


########################################
## Select Serial Port
########################################

adapters = [TinyFPGABSeries, TinyFPGAASeries]

def getProgrammerHardwareAdapter(port):
    for adapter in adapters:
        if adapter.canProgram(port):
            return adapter(port)

    return None


com_port_status_sv = StringVar(r)
com_port_status_l = Label(r, textvariable=com_port_status_sv)
com_port_status_l.grid(column=1, row=0, sticky=W+E, padx=10, pady=8)
com_port_sv = StringVar(r)
com_port_sv.set("")
select_port_om = OptionMenu(r, com_port_sv, ())
select_port_om.grid(column=0, row=0, sticky=W+E, padx=10, pady=8)
tinyfpga_adapters = dict()

tinyfpga_ports = []
def update_serial_port_list_task():
    global tinyfpga_ports
    global program_in_progress
    global tinyfpga_adapters
    
    if not program_in_progress:
        new_tinyfpga_adapters = dict((adapter.displayName(), adapter) for adapter in [getProgrammerHardwareAdapter(port) for port in comports()] if adapter is not None)
        new_tinyfpga_ports = [key for key, value in new_tinyfpga_adapters.iteritems()]
        
        if new_tinyfpga_ports != tinyfpga_ports:
            if com_port_sv.get() == "" and len(new_tinyfpga_ports) > 0:
                com_port_sv.set(new_tinyfpga_ports[0])
                update_button_state(new_serial_port_ready = True)

            update_button_state(new_serial_port_ready = com_port_sv.get() in new_tinyfpga_ports)

            menu = select_port_om["menu"]
            menu.delete(0, "end")
            for string in new_tinyfpga_ports:
                menu.add_command(
                    label=string, 
                    command=lambda value=string: com_port_sv.set(value))
            tinyfpga_ports = new_tinyfpga_ports
            tinyfpga_adapters = new_tinyfpga_adapters

    r.after(100, update_serial_port_list_task)

update_serial_port_list_task()

def check_port_status_task():
    global adapter
    try:
        adapter = tinyfpga_adapters[com_port_sv.get()]
        return adapter.checkPortStatus(update_button_state)

    except:
        com_port_status_sv.set("Unable to communicate with TinyFPGA.  Reset your TinyFPGA and check your connections.")
        traceback.print_exc()
        try:
            adapter.reset()
        except:
            traceback.print_exc()
        return False



########################################
## Select File
########################################

filename_sv = StringVar(r)

def select_bitstream_file_cmd():
    file_extensions = ('FPGA Bitstream Files', ('.hex', '.bin', '.jed'))

    try:
        adapter = tinyfpga_adapters[com_port_sv.get()]
        file_extensions = adapter.get_file_extensions()
    except:
        pass

    filename = tkFileDialog.askopenfilename(
        title = "Select file", 
        filetypes = [
            ('FPGA Bitstream Files', file_extensions), 
            ('all files', '.*')
        ]
    )

    filename_sv.set(filename)

select_file_b = Button(r, text="Select File", command=select_bitstream_file_cmd)
select_file_b.grid(column=0, row=1, sticky=W+E, padx=10, pady=8)
filename_e = Entry(r)
filename_e.config(textvariable=filename_sv)
filename_e.grid(column=1, row=1, sticky=W+E, padx=10, pady=8)

def check_bitstream_file_status_cmd(): 
    global bitstream_file_ready
    global file_mtime

    if os.path.isfile(filename_sv.get()):
        new_file_mtime = os.stat(filename_sv.get()).st_mtime

        bitstream_file_ready = True
        update_button_state()

        if new_file_mtime > file_mtime:
            program_status_sv.set("Bitstream file updated.")
        
        file_mtime = new_file_mtime

    else:
        if bitstream_file_ready:
            program_status_sv.set("Bitstream file no longer exists.")

        bitstream_file_ready = False
        update_button_state()

def check_bitstream_file_status_task():
    check_bitstream_file_status_cmd()
    r.after(1000, check_bitstream_file_status_task)

check_bitstream_file_status_task()

def check_bitstream_file_status_cb(*args):
    global file_mtime
    file_mtime = 0
    check_bitstream_file_status_cmd()

filename_sv.trace("w", check_bitstream_file_status_cb)



########################################
## Program FPGA
########################################

program_status_l = Label(r, textvariable=program_status_sv)
program_status_l.grid(column=1, row=3, sticky=W+E, padx=10, pady=8)

program_progress_pb.grid(column=1, row=2, sticky=W+E, padx=10, pady=8)

def program_fpga_thread():
    with communication_lock:
        global program_failure
        global program_in_progress
        program_failure = False

        try:
            global current_progress
            global max_progress
            global progress_lock
            with progress_lock:
                current_progress = 0

            def progress(v): 
                global progress_lock
                with progress_lock:
                    if isinstance(v, int) or isinstance(v, long):
                        global current_progress
                        current_progress += v
                    elif isinstance(v, str):
                        program_status_sv.set(v)

            adapter = tinyfpga_adapters[com_port_sv.get()]
            adapter.program(filename_sv.get(), progress)


        except:
            program_failure = True
            traceback.print_exc()

        finally:
            program_in_progress = False
            pass


current_progress = 0
max_progress = 0
progress_lock = threading.Lock()

def update_progress_task():
    global current_progress
    global max_progress
    global progress_lock

    if progress_lock.acquire(False):
        try:
            if isinstance(current_progress, (int, long)):
                program_progress_pb["value"] = current_progress
            program_progress_pb["maximum"] = max_progress
        except:
            traceback.print_exc()
        finally:
            progress_lock.release()

    r.after(100, update_progress_task)

update_progress_task()

def program_fpga_cmd():
    if check_port_status_task():
        global program_in_progress
        program_in_progress = True
        update_button_state()
        t = threading.Thread(target=program_fpga_thread)
        t.start()

program_fpga_b.configure(command=program_fpga_cmd)
program_fpga_b.grid(column=0, row=2, sticky=W+E, padx=10, pady=8)



########################################
## Boot FPGA
########################################

def boot_cmd():
    adapter = tinyfpga_adapters[com_port_sv.get()]
    adapter.exitBootloader()

boot_fpga_b.configure(command=boot_cmd)
boot_fpga_b.grid(column=0, row=3, sticky=W+E, padx=10, pady=8)

# make sure we can't get resized too small
r.update()
r.minsize(r.winfo_width(), r.winfo_height())

# start the gui
r.mainloop()
