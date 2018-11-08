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

import struct


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


class STMInfo(struct.Struct):  # Stream Info
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


class WAVInfo(struct.Struct):  # Stream Info
    def __init__(self, bom):
        super().__init__(bom + '2B2x4I')

    def data(self, data, pos):
        (self.codec,
         self.loop_flag,
         self.sample,
         self.loop_start,
         self.loop_end,
         self.reserved) = self.unpack_from(data, pos)


class TRKInfo(struct.Struct):  # Track Info
    def __init__(self, bom):
        super().__init__(bom + '2BH')

    def data(self, data, pos):
        (self.volume,
         self.pan,
         self.unk) = self.unpack_from(data, pos)


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


class Ref(struct.Struct):  # Reference
    def __init__(self, bom):
        super().__init__(bom + 'H2xi')

    def data(self, data, pos):
        (self.type_,
         self.offset) = self.unpack_from(data, pos)
