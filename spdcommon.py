import os
import sys
import subprocess
from pathlib import Path
from time import sleep

SPD_DDR5_EEPROM_SIZE = 1024
SPD_DDR5_EEPROM_PAGE_SIZE = 128
SPD_DDR5_EEPROM_BLOCK_SIZE = 64

SPD_MREG_VIRTUAL_PAGE = 0xb
SPD_MREG_RSWP_FIRST = 0xc
SPD_MREG_DATA = 0x80

SPD_IO_DELAY = 0.1 # 100 milliseconds

def optint(arg):
    return int(arg)

def opthex(arg):
    if arg[:2].lower() != '0x':
        raise ValueError('Hexadecimal argument must be preceded with "0x"')
    return int(arg, 16)

def optintx(arg):
    if arg[:2].lower() == '0x':
        return int(arg, 16)
    return int(arg, 10)

def checkroot():
    if os.getuid():
        printerr('Access is denied.')
        sys.exit(1)

def checkddr5():
    # It is not possible to check SPD ROM contents directly
    # to determinte DDR RAM type because it might be already corrupted.
    # Instead, we are querying SMBIOS to check if DDR5 RAM is in use.
    # (And it is much safer to do it like this anyway.)
    try:
        i2cproc = subprocess.Popen(['dmidecode', '--type', '17']
        , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = i2cproc.communicate(None, 10)
    except:
        printerr('`dmidecode` failure.')
        sys.exit(1)

    out = out.decode().splitlines()
    isddr5 = False
    for lns in out:
        ln = lns.strip().lower()
        pos = ln.find(':')
        if pos != -1:
            if ln[pos-4:pos] == 'type':
                if ln[-4:] == 'ddr5':
                    isddr5 = True
                    break

    if not isddr5:
        printerr('This tool is meant to be used with DDR5 RAM ONLY.')
        printerr('DO NOT attempt to force this script on any other type of DDR memory.')
        printerr('It WILL result in corruption and hardware failure of your RAM device.')
        sys.exit(1)

def readspdfile(filepath):
    pathfile = Path(filepath)
    if not pathfile.is_file():
        printerr('File not found: "{}".'.format(filepath))
        sys.exit(1)
    filesize = os.path.getsize(str(pathfile.absolute()))
    if filesize != SPD_DDR5_EEPROM_SIZE:
        printerr('SPD dump must be exactly 1024 bytes. ({})'.format(filesize))
        sys.exit(1)
    try:
        file = open(pathfile, 'rb')
    except:
        printerr('Could not open file for reading.')
        sys.exit(1)
    try:
        data = file.read(SPD_DDR5_EEPROM_SIZE)
    except:
        printerr('I/O error.')
        file.close()
        sys.exit(1)
    file.close()
    return data

BUSNUM_FOR_PAGE_RESET = None
DIMMADDR_FOR_PAGE_RESET = None
EEPROM_VIRT_PAGE_SWITCHED_FROM_ZERO = False

def selectpage(busnum, dimmaddr, pagenum):
    if pagenum < 0 or pagenum > 7:
        # This is never supposed to happen
        selectpage(busnum, dimmaddr, 0)
        sys.exit(1)
    i2cset(busnum, dimmaddr, SPD_MREG_VIRTUAL_PAGE, pagenum)
    BUSNUM_FOR_PAGE_RESET = busnum
    DIMMADDR_FOR_PAGE_RESET = dimmaddr
    EEPROM_VIRT_PAGE_SWITCHED_FROM_ZERO = pagenum != 0

def i2cget(busnum, dimmaddr, addr):
    try:
        i2cproc = subprocess.Popen(['i2cget', '-y', str(busnum), hex(dimmaddr)
        , hex(addr)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = i2cproc.communicate(None, 10)
    except:
        i2cfail('i2cget', 0)
    if i2cproc.returncode != 0:
        i2cfail('i2cget', i2cproc.returncode)
    if out[:2].decode().lower() != '0x':
        i2cfail('i2cget', 0)
    return out

def i2cset(busnum, dimmaddr, addr, byte):
    try:
        i2cproc = subprocess.Popen(['i2cset', '-y', str(busnum), hex(dimmaddr)
        , hex(addr), hex(byte)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = i2cproc.communicate(None, 10)
    except:
        i2cfail('i2cset', 0)
    if i2cproc.returncode != 0:
        i2cfail('i2cset', i2cproc.returncode)
    sleep(SPD_IO_DELAY) # writing through SMBus requires some delay
    return out

def i2cfail(tool, code):
    if code == 0:
        printerr('{} process error, aborting.'.format(tool))
    else:
        printerr('{} error ({}), aborting.'.format(tool, code))
    if EEPROM_VIRT_PAGE_SWITCHED_FROM_ZERO:
        recovered = True
        try:
            sleep(SPD_IO_DELAY)
            # Attempt to recover SPD state by switching back to first virtual page
            i2cproc = subprocess.Popen(['i2cset', '-y', str(BUSNUM_FOR_PAGE_RESET), hex(DIMMADDR_FOR_PAGE_RESET)
            , hex(SPD_MREG_VIRTUAL_PAGE), hex(0)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = i2cproc.communicate()
        except:
            recovered = False
        recovered = recovered and i2cproc.returncode == 0
        if not recovered:
            printerr('SPD EEPROM virtual page is NOT restored to first!')
    printerr('An I/O error occurred while communicating with SPD!')
    printerr('You MUST reboot the system immediately to avoid further data corruption!')
    sys.exit(1 if code == 0 else code)

def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
