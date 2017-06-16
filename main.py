#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FSTM-CSTM-FSTP Converter
# Version v1.0
# Copyright © 2017 AboodXD

# This file is part of FSTM-CSTM-FSTP Converter.

#  is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# FSTM-CSTM-FSTP Converter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, struct, sys, time

def bytes_to_string(byte):
    string = b''
    char = byte[:1]
    i = 1

    while char != b'\x00':
        string += char
        if i == len(byte): break # Prevent it from looping forever
        
        char = byte[i:i + 1]
        i += 1

    return(string.decode('utf-8'))

def to_bytes(inp, length=0, bom='>'):
    if type(inp) == bytearray:
        return bytes(inp)

    elif type(inp) == int:
        return inp.to_bytes(length, ('big' if bom == '>' else 'little'))

    elif type(inp) == str:
        outp = inp.encode('utf-8')
        outp += b'\x00' * (length - len(outp))

        return outp

class Header(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4s2xH2I2H')

    def data(self, data, pos):
        (self.magic,
        self.size_,
        self.version,
        self.fileSize,
        self.numBlocks,
        self.reserved) = self.unpack_from(data, pos)

class BLKHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI')

    def data(self, data, pos):
        (self.magic,
        self.size_) = self.unpack_from(data, pos)

class STMInfo(struct.Struct): # Stream Info
    def __init__(self, bom):
        super().__init__(bom + '3B1x11I')

    def data(self, data, pos):
        (self.codec,
        self.loop_flag,
        self.count,
        self.sample,
        self.loop_start,
        self.loop_end,
        self.sampleBlk_count,
        self.sampleBlk_size,
        self.sampleBlk_sampleCount,
        self.lSampleBlk_size,
        self.lSampleBlk_sampleCount,
        self.lSampleBlk_padSize,
        self.seek_size,
        self.SISC) = self.unpack_from(data, pos)

class TRKInfo(struct.Struct): # Track Info
    def __init__(self, bom):
        super().__init__(bom + '2B2x')

    def data(self, data, pos):
        (self.volume,
        self.pan) = self.unpack_from(data, pos)

class DSPContext(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '3H')

    def data(self, data, pos):
        (self.predictor_scale,
        self.preSample,
        self.preSample2) = self.unpack_from(data, pos)

class IMAContext(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '2H')

    def data(self, data, pos):
        (self.data_,
        self.tableIndex) = self.unpack_from(data, pos)

class Ref(struct.Struct): # Reference
    def __init__(self, bom):
        super().__init__(bom + 'H2xI')

    def data(self, data, pos):
        (self.type_,
        self.offset) = self.unpack_from(data, pos)

def convFile(f, dest):
    outputBuffer = bytearray(len(f))
    pos = 0

    if f[4:6] == b'\xFF\xFE':
        bom = '<'
    elif f[4:6] == b'\xFE\xFF':
        bom = '>'

    if dest in ["FSTM", "FSTP"]:
        dest_bom = '>'
    else:
        dest_bom = '<'
    
    header = Header(bom)
    header.data(f, pos)

    dest_ver = {"FSTM": 0x40000, "CSTM": 0x2000000, "FSTP": 0x20100}

    outputBuffer[pos:pos+header.size] = bytes(Header(dest_bom).pack(to_bytes(dest, 4), header.size_, dest_ver[dest], header.fileSize, header.numBlocks, header.reserved))
    outputBuffer[4:6] = (b'\xFE\xFF' if dest_bom == '>' else b'\xFF\xFE')

    if bytes_to_string(header.magic) not in ["FSTM", "CSTM", "FSTP"]:
        print("Unsupported file format!")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos += header.size

    sized_refs = {}
    for i in range(header.numBlocks):
        i += 1
        sized_refs[i] = Ref(bom)
        sized_refs[i].data(f, pos+12*(i-1))

        if (sized_refs[i].type_ == 0x4002) or (sized_refs[i].type_ == 0x4004):
            dest_type = {"FSTM": 0x4002, "CSTM": 0x4002, "FSTP": 0x4004}
            outputBuffer[pos+12*(i-1):pos+12*(i-1)+sized_refs[i].size] = bytes(Ref(dest_bom).pack(dest_type[dest], sized_refs[i].offset))
        else:
            outputBuffer[pos+12*(i-1):pos+12*(i-1)+sized_refs[i].size] = bytes(Ref(dest_bom).pack(sized_refs[i].type_, sized_refs[i].offset))

        sized_refs[i].block_size = struct.unpack(bom + "I", f[pos+12*(i-1)+8:pos+12*i])[0]

        outputBuffer[pos+12*(i-1)+8:pos+12*i] = to_bytes(sized_refs[i].block_size, 4, dest_bom)

    if (sized_refs[1].type_ != 0x4000) or (sized_refs[1].offset in [0xffffffff, 0]):
        print("Whoops! Fail... :D")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = sized_refs[1].offset

    info = BLKHeader(bom)
    info.data(f, pos)

    outputBuffer[pos:pos+info.size] = bytes(BLKHeader(dest_bom).pack(info.magic, info.size_))

    pos += info.size

    stmInfo_ref = Ref(bom)
    stmInfo_ref.data(f, pos)

    outputBuffer[pos:pos+stmInfo_ref.size] = bytes(Ref(dest_bom).pack(stmInfo_ref.type_, stmInfo_ref.offset))

    if (stmInfo_ref.type_ != 0x4100) or (stmInfo_ref.offset in [0xffffffff, 0]):
        print("Whoops! stmInfo_ref fail... :D")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    stmInfo_ref.pos = pos
    pos += stmInfo_ref.size

    trkInfoTable_ref = Ref(bom)
    trkInfoTable_ref.data(f, pos)

    outputBuffer[pos:pos+trkInfoTable_ref.size] = bytes(Ref(dest_bom).pack(trkInfoTable_ref.type_, trkInfoTable_ref.offset))

    if not trkInfoTable_ref.type_ in [0x0101, 0]:
        print("Whoops! trkInfoTable_ref fail... :D")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos += trkInfoTable_ref.size

    channelInfoTable_ref = Ref(bom)
    channelInfoTable_ref.data(f, pos)

    outputBuffer[pos:pos+channelInfoTable_ref.size] = bytes(Ref(dest_bom).pack(channelInfoTable_ref.type_, channelInfoTable_ref.offset))

    if channelInfoTable_ref.type_ != 0x0101:
        print("Whoops! channelInfo_ref fail... :D")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pos = stmInfo_ref.offset + stmInfo_ref.pos
    stmInfo = STMInfo(bom)
    stmInfo.data(f, pos)

    outputBuffer[pos:pos+stmInfo.size] = bytes(STMInfo(dest_bom).pack(stmInfo.codec, stmInfo.loop_flag, stmInfo.count, stmInfo.sample, stmInfo.loop_start, stmInfo.loop_end, stmInfo.sampleBlk_count, stmInfo.sampleBlk_size, stmInfo.sampleBlk_sampleCount, stmInfo.lSampleBlk_size, stmInfo.lSampleBlk_sampleCount, stmInfo.lSampleBlk_padSize, stmInfo.seek_size, stmInfo.SISC))

    pos += stmInfo.size

    sampleData_ref = Ref(bom)
    sampleData_ref.data(f, pos)

    outputBuffer[pos:pos+sampleData_ref.size] = bytes(Ref(dest_bom).pack(sampleData_ref.type_, sampleData_ref.offset))

    pos += 8

    trkInfoTable = {}
    trkInfo = {}

    if not trkInfoTable_ref.offset in [0xffffffff, 0]:
        pos = trkInfoTable_ref.offset + stmInfo_ref.pos
        count = struct.unpack(bom + "I", f[pos:pos+4])[0]
        outputBuffer[pos:pos+4] = to_bytes(count, 4, dest_bom)
        pos += 4
        for i in range(count):
            i += 1
            pos = trkInfoTable_ref.offset + stmInfo_ref.pos + 4
            trkInfoTable[i] = Ref(bom)
            trkInfoTable[i].data(f, pos+8*(i-1))
            outputBuffer[pos+8*(i-1):pos+8*(i-1)+trkInfoTable[i].size] = bytes(Ref(dest_bom).pack(trkInfoTable[i].type_, trkInfoTable[i].offset))
            if trkInfoTable[i].offset not in [0xffffffff, 0]:
                pos = trkInfoTable[i].offset + pos-4
                trkInfo[i] = TRKInfo(bom)
                trkInfo[i].data(f, pos)
                outputBuffer[pos:pos+trkInfo[i].size] = bytes(TRKInfo(dest_bom).pack(trkInfo[i].volume, trkInfo[i].pan))
                pos += trkInfo[i].size
                channelIndexByteTable_ref = Ref(bom)
                channelIndexByteTable_ref.data(f, pos)
                outputBuffer[pos:pos+channelIndexByteTable_ref.size] = bytes(Ref(dest_bom).pack(channelIndexByteTable_ref.type_, channelIndexByteTable_ref.offset))
                if channelIndexByteTable_ref.offset not in [0xffffffff, 0]:
                    pos = channelIndexByteTable_ref.offset + pos-trkInfo[i].size
                    count = struct.unpack(bom + "I", f[pos:pos+4])[0]
                    outputBuffer[pos:pos+4] = to_bytes(count, 4, dest_bom)
                    pos += 4
                    elem = f[pos:pos+count]
                    outputBuffer[pos:pos+count] = elem

    channelInfoTable = {}
    ADPCMInfo_ref = {}
    param = {}

    pos = channelInfoTable_ref.offset + stmInfo_ref.pos
    count = struct.unpack(bom + "I", f[pos:pos+4])[0]
    outputBuffer[pos:pos+4] = to_bytes(count, 4, dest_bom)
    pos += 4
    for i in range(count):
        i += 1
        pos = channelInfoTable_ref.offset + stmInfo_ref.pos + 4
        channelInfoTable[i] = Ref(bom)
        channelInfoTable[i].data(f, pos+8*(i-1))
        outputBuffer[pos+8*(i-1):pos+8*(i-1)+channelInfoTable[i].size] = bytes(Ref(dest_bom).pack(channelInfoTable[i].type_, channelInfoTable[i].offset))
        if channelInfoTable[i].offset not in [0xffffffff, 0]:
            pos = channelInfoTable[i].offset + pos-4
            ADPCMInfo_ref[i] = Ref(bom)
            ADPCMInfo_ref[i].data(f, pos)
            outputBuffer[pos:pos+ADPCMInfo_ref[i].size] = bytes(Ref(dest_bom).pack(ADPCMInfo_ref[i].type_, ADPCMInfo_ref[i].offset))
            if ADPCMInfo_ref[i].offset not in [0xffffffff, 0]:
                pos = ADPCMInfo_ref[i].offset + pos
                if ADPCMInfo_ref[i].type_ == 0x0300:
                    for i in range(16):
                        i += 1
                        param[i] = struct.unpack(bom + "H", f[pos+2*(i-1):pos+2*(i-1)+2])[0]
                        outputBuffer[pos+2*(i-1):pos+2*(i-1)+2] = to_bytes(param[i], 2, dest_bom)
                    pos += 32
                    context = DSPContext(bom)
                    context.data(f, pos)
                    outputBuffer[pos:pos+context.size] = bytes(DSPContext(dest_bom).pack(context.predictor_scale, context.preSample, context.preSample2))
                    pos += context.size
                    loopContext = DSPContext(bom)
                    loopContext.data(f, pos)
                    outputBuffer[pos:pos+loopContext.size] = bytes(DSPContext(dest_bom).pack(loopContext.predictor_scale, loopContext.preSample, loopContext.preSample2))
                    pos += loopContext.size
                    pos += 2
                elif ADPCMInfo_ref[i].type_ == 0x0301:
                    context = IMAContext(bom)
                    context.data(f, pos)
                    outputBuffer[pos:pos+context.size] = bytes(IMAContext(dest_bom).pack(context.data_, context.tableIndex))
                    pos += context.size
                    loopContext = IMAContext(bom)
                    loopContext.data(f, pos)
                    outputBuffer[pos:pos+loopContext.size] = bytes(IMAContext(dest_bom).pack(loopContext.data_, loopContext.tableIndex))
                    pos += loopContext.size

    for i in range(header.numBlocks):
        i += 1
        if sized_refs[i].offset not in [0xffffffff, 0]:
            if sized_refs[i].type_ == 0x4001:
                pos = sized_refs[i].offset
                seek = BLKHeader(bom)
                seek.data(f, pos)
                outputBuffer[pos:pos+seek.size] = bytes(BLKHeader(dest_bom).pack(seek.magic, seek.size_))
                pos += seek.size
                seek.data_ = f[pos:pos+seek.size_-8]
                outputBuffer[pos:pos+seek.size_-8] = seek.data_
            elif (sized_refs[i].type_ == 0x4002) or (sized_refs[i].type_ == 0x4004):
                dest_dataHead = {"FSTM": b'DATA', "CSTM": b'DATA', "FSTP": b'PDAT'}
                pos = sized_refs[i].offset
                data = BLKHeader(bom)
                data.data(f, pos)
                outputBuffer[pos:pos+data.size] = bytes(BLKHeader(dest_bom).pack(dest_dataHead[dest], data.size_))
                pos += data.size
                data.data_ = f[pos:pos+data.size_-8]
                outputBuffer[pos:pos+data.size_-8] = data.data_
            else:
                pass

    return outputBuffer

def main():
    print("FSTM-CSTM-FSTP Converter v1.0")
    print("(C) 2017 AboodXD")

    if len(sys.argv) != 3:
        print('')
        print("Usage: main [input] dest_format")
        print('')
        print("Supported dest formats:")
        print("FSTM")
        print("CSTM")
        print("FSTP")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    with open(sys.argv[1], "rb") as inf:
        inb = inf.read()
        inf.close()

    if sys.argv[2] not in ["FSTM", "CSTM", "FSTP"]:
        print("Unsupported destination format!")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    dest = sys.argv[2]

    outputBuffer = convFile(inb, dest)

    name = os.path.splitext(sys.argv[1])[0]

    dest_ext = {"FSTM": ".bfstm", "CSTM": ".bcstm", "FSTP": ".bfstp"}

    with open(name + dest_ext[dest], "wb+") as out:
        out.write(outputBuffer)

if __name__ == '__main__': main()
