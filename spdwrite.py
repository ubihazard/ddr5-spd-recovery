#!/usr/bin/python

import os
import sys
import getopt
from functools import cmp_to_key

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
    rstr = ''
    for opt, arg in opts:
        try:
            if opt in ('-h', '--help'):
                print(sys.argv[0], '--bus <busnum> --dimm <dimmaddr> --file <dump> --range <0..1023>[,0-1023[,...]]')
                print('  -b --bus: bus number (0)')
                print('  -d --dimm: dimm address on the bus (0x51)')
                print('  -f --file: clean SPD dump in raw binary format.')
                print('  --range: specific region(s) to overwrite.')
                print('    (Ranges must not overlap.)')
                sys.exit(0)
            elif opt in ('-b', '--bus'):
                bus = optint(arg)
            elif opt in ('-d', '--dimm'):
                dimm = opthex(arg)
            elif opt in ('-f', '--file'):
                dump = arg
            elif opt in ('--range'):
                rstr = arg
        except:
            usage()
    if bus < 0 or bus > 99 \
    or dimm < 0x50 or dimm > 0x57 \
    or dump == '':
        usage()
    ranges = getranges(rstr)
    if len(ranges) == 0:
        usage()

    checkroot()
    checkddr5()
    writespd(bus, dimm, dump, ranges)

def rangesortfunc(a, b):
    return a[0] - b[0]

def getranges(rstr):
    if rstr == '':
        return [[0, SPD_DDR5_EEPROM_SIZE - 1]]
    rngv = []
    rngs = rstr.split(',')
    if len(rngs) > SPD_DDR5_EEPROM_SIZE:
        return []
    for item in rngs:
        rng = item.split('-')
        first = optintx(rng[0])
        last = first
        if len(rng) > 1:
            if len(rng) > 2:
                return []
            last = optintx(rng[1])
        if first < 0 or first > 1023 \
        or last < first or last > 1023:
            return []
        rngv.append([first, last])
    # Find duplicates or overlapping regions
    if len(rngv) == 0:
        return []
    rngv = sorted(rngv, key=cmp_to_key(rangesortfunc))
    for idx in range(0, len(rngv) - 1):
        if rngv[idx][0] <= rngv[idx + 1][0] <= rngv[idx][1]:
            return []
    return rngv

def rswpblocksget(busnum, dimmaddr):
    rswpblocks = []
    for reg in range(0, 2):
        out = i2cget(busnum, dimmaddr, SPD_MREG_RSWP_FIRST + reg)
        out = out[2:].decode()
        byte = bytes.fromhex(out)[0]
        for bit in range(0, 8):
            rswpblocks.append(bool((byte >> bit) & 1))

def writespd(busnum, dimmaddr, filepath, ranges):
    spddata = readspdfile(filepath)

    print('WARNING! Improper use of this tool can result in data corruption over SMBus and hardware failure.\n')
    print('Will now write to device file /dev/i2c-{}, chip address {}, byte-by-byte.\n'
    .format(busnum, hex(dimmaddr)))

    go = input('Continue? (yes/no): ').lower()
    print('')
    if go in ['yes']:
        page = -1
        rswpblocks = rswpblocksget(busnum, dimmaddr)
        for rng in ranges:
            start = rng[0]
            end = rng[1]
            for idx in range(start, end + 1):
                block = idx / SPD_DDR5_EEPROM_BLOCK_SIZE
                pagenew = idx / SPD_DDR5_EEPROM_PAGE_SIZE
                off = idx % SPD_DDR5_EEPROM_PAGE_SIZE
                addr = SPD_MREG_DATA | off
                byte = spddata[idx]
                if rswpblocks[block]:
                    print('Write-protected: {}/{}, {} -> {}.{} [{}]'.format(idx + 1, end + 1, hex(byte), page - 1, hex(addr), hex(idx)))
                    continue
                if pagenew != page:
                    page = pagenew
                    selectpage(busnum, dimmaddr, page)
                print('Writing to SPD EEPROM: {}/{}, {} -> {}.{} [{}]'.format(idx + 1, end + 1, hex(byte), page - 1, hex(addr), hex(idx)))
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
