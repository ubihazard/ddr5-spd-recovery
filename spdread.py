#!/usr/bin/python

import os
import sys
import getopt
from pathlib import Path

def usage():
    printerr(sys.argv[0], '--bus <busnum> --dimm <dimmaddr> --help')
    sys.exit(1)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'b:d:h', ['bus=', 'dimm=', 'help'])
    except getopt.GetoptError:
        usage()

    bus = -1
    dimm = -1
    for opt, arg in opts:
        try:
            if opt in ('-h', '--help'):
                print(sys.argv[0], '--bus <busnum> --dimm <dimmaddr>')
                print('  -b --bus: bus number (0)')
                print('  -d --dimm: dimm address on the bus (0x51)')
                sys.exit(0)
            elif opt in ('-b', '--bus'):
                bus = optint(arg)
            elif opt in ('-d', '--dimm'):
                dimm = opthex(arg)
        except:
            usage()
    if bus < 0 or bus > 99 \
    or dimm < 0x50 or dimm > 0x57:
        usage()

    checkroot()
    checkddr5()
    readspd(bus, dimm)

EEPROM_DUMP_FILE_EXT = 'spd'

def readspd(busnum, dimmaddr):
    if not os.access('./', os.W_OK):
        printerr('Current directory is not writable.')
        sys.exit(1)
    filepath = './dimm{}.{}'.format(dimmaddr, EEPROM_DUMP_FILE_EXT)
    pathfile = Path(filepath)
    try:
        spdfile = open(pathfile, 'wb')
    except:
        printerr('Could not open file "{}" for writing.'.format(filepath))
        sys.exit(1)

    print('WARNING! Improper use of this tool can result in data corruption over SMBus and hardware failure.\n')
    print('Will now read/write from/to device file /dev/i2c-{}, chip address {}, byte-by-byte.\n'
    .format(busnum, hex(dimmaddr)))

    go = input('Continue? (yes/no): ').lower()
    print('')
    if go in ['yes']:
        page = 0
        start = 0
        end = SPD_DDR5_EEPROM_SIZE
        ioerr = False
        for idx in range(start, end):
            off = idx % SPD_DDR5_EEPROM_PAGE_SIZE
            addr = SPD_MREG_DATA | off
            if off == 0:
                selectpage(busnum, dimmaddr, page)
                page += 1
            out = i2cget(busnum, dimmaddr, addr)
            out = out[2:].decode()       # strip "0x" and convert to string
            byte = bytes.fromhex(out)[0] # convert hex string to bytes
            print('Reading from SPD EEPROM: {}/{}, {}.{} [{}]: {}'.format(idx + 1, end, page - 1, hex(addr), hex(idx), hex(byte)))
            try:
                spdfile.write(bytes([byte]))
            except:
                ioerr = True
                printerr('I/O error.')
                break
        selectpage(busnum, dimmaddr, 0)
        spdfile.close()
        if ioerr:
            sys.exit(1)
        print('')
        print('SPD EEPROM contents from DIMM {} written to: "{}".'.format(hex(dimmaddr), filepath))
    else:
        print('Exiting without performing any operations on SMBus.')
        sys.exit(0)

if __name__ == '__main__':
    if __package__ == None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from spdcommon import optint, opthex, checkroot, checkddr5, selectpage, i2cget, printerr \
    , SPD_MREG_DATA, SPD_DDR5_EEPROM_SIZE, SPD_DDR5_EEPROM_PAGE_SIZE
    main(sys.argv[1:])
