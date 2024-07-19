#!/usr/bin/python

import os
import sys
import getopt

def usage():
    printerr(sys.argv[0], '--bus <busnum> --dimm <dimmaddr> --first <0..15> --last <0..15> --help')
    sys.exit(1)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'b:d:f:l:h', ['bus=', 'dimm=', 'first=', 'last=', 'help'])
    except getopt.GetoptError:
        usage()

    bus = -1
    dimm = -1
    first = -1
    last = -1
    for opt, arg in opts:
        try:
            if opt in ('-h', '--help'):
                print(sys.argv[0], '--bus <busnum> --dimm <dimmaddr> --first <0..15> --last <0..15>')
                print('  -b --bus: bus number (0)')
                print('  -d --dimm: dimm address on the bus (0x51)')
                print('  -f --first: first block to protect (0)')
                print('  -l --last: last block to protect (9)')
                sys.exit(0)
            elif opt in ('-b', '--bus'):
                bus = optint(arg)
            elif opt in ('-d', '--dimm'):
                dimm = opthex(arg)
            elif opt in ('-f', '--first'):
                first = optint(arg)
            elif opt in ('-l', '--last'):
                last = optint(arg)
        except:
            usage()
    if bus < 0 or bus > 99 \
    or dimm < 0x50 or dimm > 0x57 \
    or first < 0 or first > 15 \
    or last < first or last > 15:
        usage()

    checkroot()
    checkddr5()
    setrswp(bus, dimm, first, last)

def setrswp(busnum, dimmaddr, blockfrom, blockto):
    print('WARNING! Improper use of this tool can result in data corruption over SMBus and hardware failure.\n')
    print('Will now read/write from/to device file /dev/i2c-{}, chip address {}, byte-by-byte.\n'
    .format(busnum, hex(dimmaddr)))

    go = input('Continue? (yes/no): ').lower()
    print('')
    if go in ['yes']:
        print('DANGER!!! RSWP status bit cannot be cleared through mainboard SMBus controller!')
        print('If you set protection bit for the wrong data block or on the wrong DIMM, you will need a dedicated hardware DDR5 RAM programmer device to remove it!')
        print('Likewise, setting protection bit on the part of SPD EEPROM contents which is corrupted will leave the RAM module in a permanently broken state!')
        print('')
        print('To avoid setting RSWP on the wrong RAM module, boot your system with a single perfectly working RAM stick with its SPD ROM contents in ideal state (preferably with proper unique serial number). Make sure the SPD ROM passes all CRC checks. If in doubt, make a dump using `spdread.py` and run it through `spdinfo.py`.')
        print('')
        print('Setting RSWP bit for blocks #{}..{} on DIMM {}.'.format(blockfrom, blockto, hex(dimmaddr)))
        print('')
        go = input('Really continue? (yes/no): ').lower()
        print('')
    if go in ['yes']:
        print('Last call. Are you *absolutely* sure?')
        print('')
        print('Setting RSWP bit for blocks #{}..{} on DIMM {}.'.format(blockfrom, blockto, hex(dimmaddr)))
        print('')
        go = input('REALLY continue? (yes/no): ').lower()
        print('')
    if go in ['yes']:
        for idx in range(blockfrom, blockto + 1):
            rswpblockset(busnum, dimmaddr, idx)
        print('')
        print('RSWP is now set for blocks #{}..{} on DIMM {}.'.format(blockfrom, blockto, hex(dimmaddr)))
        print('')
        print('This protection can only be removed using a dedicated hardware DDR5 RAM programmer device.')
        print('You have been warned.')
    else:
        print('Exiting without performing any operations on SMBus.')
        sys.exit(0)

def rswpblockset(busnum, dimmaddr, block):
    mreg = SPD_MREG_RSWP_FIRST + int(block >= 8)
    blockidx = block % 8
    out = i2cget(busnum, dimmaddr, mreg)
    out = out[2:].decode()
    oldbyte = bytes.fromhex(out)[0]
    if (oldbyte >> blockidx) & 1 == 0:
        newbyte = oldbyte | (1 << blockidx)
        print('Setting RSWP bit for block {0: >3} (register {1}, {2} -> {3})'
        .format('#' + str(block), hex(mreg), hex(oldbyte), hex(newbyte)))
        # DANGER: no way back after this!
        i2cset(busnum, dimmaddr, mreg, newbyte)

if __name__ == '__main__':
    if __package__ == None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from spdcommon import optint, opthex, checkroot, checkddr5, i2cget, i2cset, printerr \
    , SPD_MREG_RSWP_FIRST
    main(sys.argv[1:])
