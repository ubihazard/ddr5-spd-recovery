#!/usr/bin/python

import os
import sys
import getopt

def usage():
    printerr(sys.argv[0], '--bus <busnum> --dimm <dimmaddr> --file <dump> --range <0..1023>[,0-1023[,...]] --help')
    sys.exit(1)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'b:d:f:h', ['bus=', 'dimm=', 'file=', 'range=', 'help'])
    except getopt.GetoptError:
        usage()

    bus = -1
    dimm = -1
    dump = ''
    rnge = ''
    for opt, arg in opts:
        try:
            if opt in ('-h', '--help'):
                print(sys.argv[0], '--bus <busnum> --dimm <dimmaddr> --file <dump>')
                print('  -b --bus: bus number (0)')
                print('  -d --dimm: dimm address on the bus (0x51)')
                print('  -f --file: clean SPD dump in raw binary format.')
                print('  --range: specific region(s) to write.')
                sys.exit(0)
            elif opt in ('-b', '--bus'):
                bus = optint(arg)
            elif opt in ('-d', '--dimm'):
                dimm = opthex(arg)
            elif opt in ('-f', '--file'):
                dump = arg
            elif opt in ('--range'):
                rnge = arg
        except:
            usage()
    if bus < 0 or bus > 99 \
    or dimm < 0x50 or dimm > 0x57 \
    or dump == '':
        usage()

    checkroot()
    checkddr5()
    writespd(bus, dimm, dump)

def writespd(busnum, dimmaddr, filepath):
    spddata = readspdfile(filepath)

    print('WARNING! Improper use of this tool can result in data corruption over SMBus and hardware failure.\n')
    print('Will now write to device file /dev/i2c-{}, chip address {}, byte-by-byte.\n'
    .format(busnum, hex(dimmaddr)))

    go = input('Continue? (yes/no): ').lower()
    print('')
    if go in ['yes']:
        page = 0
        start = 0
        end = SPD_DDR5_EEPROM_SIZE
        for idx in range(start, end):
            off = idx % SPD_DDR5_EEPROM_PAGE_SIZE
            addr = SPD_MREG_DATA | off
            if off == 0:
                selectpage(busnum, dimmaddr, page)
                page += 1
            byte = spddata[idx]
            print('Writing to SPD EEPROM: {}/{} ({} -> {}.{})'.format(idx + 1, end, hex(byte), page - 1, hex(addr)))
            i2cset(busnum, dimmaddr, addr, byte)
        selectpage(busnum, dimmaddr, 0)
        print('')
        print('Successfully flashed "{}" to DIMM {}.'.format(filepath, hex(dimmaddr)))
    else:
        print('Exiting without performing any operations on SMBus.')
        sys.exit(0)

if __name__ == '__main__':
    if __package__ == None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from spdcommon import optint, opthex, checkroot, checkddr5, readspdfile, selectpage, i2cset, printerr \
    , SPD_MREG_DATA, SPD_DDR5_EEPROM_SIZE, SPD_DDR5_EEPROM_PAGE_SIZE
    main(sys.argv[1:])
