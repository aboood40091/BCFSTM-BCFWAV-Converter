#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BCFSTM-BCFWAV Converter
# Version v2.1
# Copyright © 2017-2018 AboodXD

# This file is part of BCFSTM-BCFWAV Converter.

#  is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BCFSTM-BCFWAV Converter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time

from bytes import bytes_to_string
from structs import struct, Header, BLKHeader, WAVInfo
from structs import DSPContext, IMAContext, Ref


def readFile(f):
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'

    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    else:
        print("\nInvalid BOM!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    header = Header(bom)
    header.data(f, pos)

    if bytes_to_string(header.magic) not in ["FWAV", "CWAV"]:
        print("\nUnsupported file format!")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)
    
    print("\nMagic: " + bytes_to_string(header.magic))
    print("Header size: " + hex(header.size_))
    print("File version: " + hex(header.version))
    print("File size: " + hex(header.fileSize))
    print("Number of blocks: " + str(header.numBlocks))

    pos += header.size
    sized_refs = {}

    for i in range(1, header.numBlocks + 1):
        sized_refs[i] = Ref(bom)
        sized_refs[i].data(f, pos + 12 * (i - 1))
        sized_refs[i].block_size = struct.unpack(bom + "I", f[pos + 12 * (i - 1) + 8:pos + 12 * i])[0]

        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ == 0x7000:
                print("\nInfo Block offset: " + hex(sized_refs[i].offset))

            elif sized_refs[i].type_ == 0x7001:
                print("\nData Block offset: " + hex(sized_refs[i].offset))

            else:
                print("\n" + hex(sized_refs[i].type_) + " Block offset: " + hex(sized_refs[i].offset))

            print("Size: " + hex(sized_refs[i].block_size))

    if sized_refs[1].type_ != 0x7000 or sized_refs[1].offset in [0, -1]:
        print("\nSomething went wrong!\nError code: 5")
        print("\nExiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)
    info.pos = pos

    print("\nInfo Block Magic: " + bytes_to_string(info.magic))
    print("Size: " + hex(info.size_))

    pos += info.size

    wavInfo = WAVInfo(bom)
    wavInfo.data(f, pos)

    codec = {0: "PCM8", 1: "PCM16", 2: "DSP ADPCM", 3: "IMA ADPCM"}
    if wavInfo.codec in codec:
        print("\nEncoding: " + codec[wavInfo.codec])

    else:
        print("\nEncoding: " + str(wavInfo.codec))

    print("Loop Flag: " + str(wavInfo.loop_flag))
    print("Sample Rate: " + str(wavInfo.sample))
    print("Loop Start Frame: " + str(wavInfo.loop_start))
    print("Loop End Frame: " + str(wavInfo.loop_end))

    pos += wavInfo.size

    channelInfoTable = {}
    ADPCMInfo_ref = {}

    count = struct.unpack(bom + "I", f[pos:pos + 4])[0]
    print("Channel Count: " + str(count))
    countPos = pos

    for i in range(1, count + 1):
        pos = countPos + 4
        channelInfoTable[i] = Ref(bom)
        channelInfoTable[i].data(f, pos + 8 * (i - 1))

        if channelInfoTable[i].offset not in [0, -1]:
            pos = channelInfoTable[i].offset + countPos
            print("\nChannel " + str(i) + " Info Entry offset: " + hex(pos))

            sampleData_ref = Ref(bom)
            sampleData_ref.data(f, pos)

            if sampleData_ref.offset not in [0, -1]:
                for z in range(1, header.numBlocks + 1):
                    if sized_refs[z].offset not in [0, -1]:
                        if sized_refs[z].type_ == 0x7001:
                            print("\nChannel " + str(i) + " Info Entry Sample Data offset: " + hex(sampleData_ref.offset + sized_refs[z].offset + 8))

            pos += 8

            print("\nChannel " + str(i) + " Info Entry ADPCM Info Reference offset: " + hex(pos))

            ADPCMInfo_ref[i] = Ref(bom)
            ADPCMInfo_ref[i].data(f, pos)

            if ADPCMInfo_ref[i].offset not in [0, -1]:
                print("\nADPCM Info offset: " + hex(ADPCMInfo_ref[i].offset + pos - 8))
                print("Type: " + hex(ADPCMInfo_ref[i].type_))

                pos = ADPCMInfo_ref[i].offset + pos - 8
                if ADPCMInfo_ref[i].type_ == 0x0300:
                    param = b''
                    for i in range(1, 17):
                        param += struct.unpack(bom + "H", f[pos + 2 * (i - 1):pos + 2 * (i - 1) + 2])[0].to_bytes(2, 'big')

                    print("Param: " + str(param))

                    pos += 32
                    context = DSPContext(bom)
                    context.data(f, pos)

                    print("Context Predictor and Scale: " + hex(context.predictor_scale))
                    print("Context Previous Sample: " + hex(context.preSample))
                    print("Context Second Previous Sample: " + hex(context.preSample2))

                    pos += context.size
                    loopContext = DSPContext(bom)
                    loopContext.data(f, pos)

                    print("Loop Context Predictor and Scale: " + hex(loopContext.predictor_scale))
                    print("Loop Context Previous Sample: " + hex(loopContext.preSample))
                    print("Loop Context Second Previous Sample: " + hex(loopContext.preSample2))

                    pos += loopContext.size
                    pos += 2

                elif ADPCMInfo_ref[i].type_ == 0x0301:
                    context = IMAContext(bom)
                    context.data(f, pos)

                    print("Context Data: " + hex(context.data_))
                    print("Context Table Index: " + hex(context.tableIndex))

                    pos += context.size
                    loopContext = IMAContext(bom)
                    loopContext.data(f, pos)

                    print("Loop Context Data: " + hex(loopContext.data_))
                    print("Loop Context Table Index: " + hex(loopContext.tableIndex))

                    pos += loopContext.size

    for i in range(1, header.numBlocks + 1):
        if sized_refs[i].offset not in [0, -1]:
            if sized_refs[i].type_ == 0x7001:
                pos = sized_refs[i].offset
                data = BLKHeader(bom)
                data.data(f, pos)

                print("\nData Block Magic: " + bytes_to_string(data.magic))
                print("Size: " + hex(data.size_))

                pos += data.size
                data.data_ = f[pos:pos+data.size_ - 8]

def main():
    with open(sys.argv[1], "rb") as inf:
        inb = inf.read()
        inf.close()
                    
    readFile(inb)

if __name__ == '__main__': main()
