#!/usr/bin/python

import os
import sys
import getopt

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
    checkrswp(bus, dimm)

def checkrswp(busnum, dimmaddr):
    print('WARNING! Improper use of this tool can result in data corruption over SMBus and hardware failure.\n')
    print('Will now read from device file /dev/i2c-{}, chip address {}, byte-by-byte.\n'
    .format(busnum, hex(dimmaddr)))

    go = input('Continue? (yes/no): ').lower()
    print('')
    if go in ['yes']:
        print('RSWP status for blocks #{}..{} on DIMM {}:'.format(0, 15, hex(dimmaddr)))
        for idx in range(0, 15 + 1):
            rswpblockget(busnum, dimmaddr, idx)
    else:
        print('Exiting without performing any operations on SMBus.')
        sys.exit(0)

RSWP_STATUS = ['writable', 'protected'];

def rswpblockget(busnum, dimmaddr, block):
    mreg = SPD_MREG_RSWP_FIRST + int(block >= 8)
    blockidx = block % 8
    out = i2cget(busnum, dimmaddr, mreg)
    out = out[2:].decode()
    byte = bytes.fromhex(out)[0]
    print('Block {0: >3} RSWP status: {1}'.format('#' + str(block)
    , RSWP_STATUS[(byte >> blockidx) & 1]))

if __name__ == '__main__':
    if __package__ == None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from spdcommon import optint, opthex, checkroot, checkddr5, i2cget, printerr \
    , SPD_MREG_RSWP_FIRST
    main(sys.argv[1:])
