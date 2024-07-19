#!/usr/bin/python

import os
import sys
import getopt
import datetime

SPD_DDR5_TYPE = 0x12
SPD_DDR_TYPE_OFFSET = 2

SPD_MANUF_ID_OFFSET = 512
SPD_MANUF_ID_LENGTH = 2
SPD_MANUF_DATE_OFFSET = 515
SPD_MANUF_DATE_LENGTH = 2

SPD_SN_OFFSET = 517
SPD_SN_LENGTH = 4
SPD_PN_OFFSET = 521
SPD_PN_LENGTH = 30

SPD_XMP30_OFFSET = 640
SPD_XMP30_HEADER_LENGTH = 64
SPD_XMP30_PROFILE_LENGTH = 64 # up to five XMP 3.0 profiles plus header section
SPD_XMP30_PROFILE_PRESENT = 0x30

SPD_EXPO_OFFSET = 832
SPD_EXPO_SECTION_LENGTH = 128

def usage():
    printerr(sys.argv[0], '--file <dump> --fixcrc --help')
    sys.exit(1)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'f:h', ['file=', 'help', 'fixcrc'])
    except getopt.GetoptError:
        usage()

    dump = ''
    fixcrc = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(sys.argv[0], '--file <dump> --fixcrc')
            print('  -f --file: SPD dump in raw binary format.')
            print('  --fixcrc: calculate new CRC checksum(s).')
            print('    (Will write fixed SPD dump to `stdout`.)')
            sys.exit(0)
        elif opt in ('-f', '--file'):
            dump = arg
        elif opt in ('--fixcrc'):
            fixcrc = True
    if dump == '':
        usage()

    analyzespd(dump, fixcrc)

def analyzespd(filepath, fixcrc):
    spddata = readspdfile(filepath)

    ddrv = spddata[SPD_DDR_TYPE_OFFSET]
    if ddrv != SPD_DDR5_TYPE:
        printerr("SPD dump doesn't appear to be from DDR5 memory.")
        sys.exit(1)

    if not fixcrc:
        # Manufacturer
        mid = spddata[SPD_MANUF_ID_OFFSET:SPD_MANUF_ID_OFFSET + SPD_MANUF_ID_LENGTH]
        print('Manufacturer: {}'.format(mid.hex()))

        # Date of production
        myear = bcd(spddata[SPD_MANUF_DATE_OFFSET])
        mweek = bcd(spddata[SPD_MANUF_DATE_OFFSET + 1])
        if mweek < 1 or mweek > 52:
            mdate = '?'
        else:
            date = datetime.datetime.strptime('{} {} 1'.format(2000 + myear, mweek), '%Y %W %w')
            mdate = date.strftime('%-d %b')
        print('Produced: {}/{} ({})'.format(mweek, 2000 + myear, mdate))

        # Serial and part numbers
        sn = spddata[SPD_SN_OFFSET:SPD_SN_OFFSET + SPD_SN_LENGTH]
        print('S/N: {}'.format(sn.hex()))
        pn = spddata[SPD_PN_OFFSET:SPD_PN_OFFSET + SPD_PN_LENGTH]
        print('P/N: {}'.format(pn.decode().strip()))

    # Calculate CRC checksums
    start = 0
    end = SPD_MANUF_ID_OFFSET
    crc = calccrc(spddata, start, end)
    crcfail = False
    if fixcrc:
        putcrc(spddata, start, end - start, crc)
    else:
        crcdump = getcrc(spddata, start, end - start)
        crcfail = crcfail or crcdump != crc
        print('Main CRC: {} ({})'.format(hex(crcdump), hex(crc)))
    if xmppresent(spddata):
        for n in range(1, 6):
            if xmpprofilepresent(spddata, n):
                start = SPD_XMP30_OFFSET + n * SPD_XMP30_PROFILE_LENGTH
                end = start + SPD_XMP30_PROFILE_LENGTH
                crc = calccrc(spddata, start, end)
                if fixcrc:
                    putcrc(spddata, start, end - start, crc)
                else:
                    crcdump = getcrc(spddata, start, end - start)
                    crcfail = crcfail or crcdump != crc
                    print('  XMP profile #{} CRC: {} ({})'.format(n, hex(crcdump), hex(crc)))
    if expopresent(spddata):
        start = SPD_EXPO_OFFSET
        end = start + SPD_EXPO_SECTION_LENGTH
        crc = calccrc(spddata, start, end)
        if fixcrc:
            putcrc(spddata, start, end - start, crc)
        else:
            crcdump = getcrc(spddata, start, end - start)
            crcfail = crcfail or crcdump != crc
            print('  EXPO CRC: {} ({})'.format(hex(crcdump), hex(crc)))

    # Write SPD with fixed CRCs to stdout
    if fixcrc:
        sys.stdout.buffer.write(spddata)
    elif crcfail:
        printerr('\nWARNING: CRC mismatch!')

def xmppresent(data):
    off = SPD_XMP30_OFFSET
    return data[off] == 0xc and data[off + 1] == 0x4a

def xmpprofilepresent(data, num):
    off = SPD_XMP30_OFFSET + num * SPD_XMP30_PROFILE_LENGTH
    return data[off] == SPD_XMP30_PROFILE_PRESENT

def expopresent(data):
    off = SPD_EXPO_OFFSET
    return data[off + 0] == ord('E') and data[off + 1] == ord('X') \
    and    data[off + 2] == ord('P') and data[off + 3] == ord('O')

def getcrc(data, blockoff, blocklen):
    return (data[blockoff + blocklen - 1] << 8) | data[blockoff + blocklen - 2]

def putcrc(data, blockoff, blocklen, crc):
    data[blockoff + blocklen - 2] = crc & 0xff
    data[blockoff + blocklen - 1] = crc >> 8

def calccrc(data, start, end):
    crc = 0
    # Exclude last 2 bytes: do not include CRC itself
    # in new CRC computation
    for i in range(start, end - 2):
        crc = crc16(crc, data[i])
    return crc

SPD_CRC_POLY = 0x1021

def crc16(crc, byte):
    crc ^= byte << 8
    for i in range(0, 8):
        crc = (crc << 1) ^ (SPD_CRC_POLY if crc >> 15 else 0)
        crc &= 0xffff
    return crc

def bcd(byte):
    return (byte >> 4) * 10 + (byte & 0xf)

if __name__ == '__main__':
    if __package__ == None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from spdcommon import readspdfile, printerr
    main(sys.argv[1:])
