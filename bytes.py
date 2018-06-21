#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BCFSTM-BCFWAV Converter
# Version v2.0
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

def bytes_to_string(data):
    end = data.find(b'\0')
    if end == -1:
        return data.decode('utf-8')

    return data[:end].decode('utf-8')


def to_bytes(inp, length=1, bom='>'):
    if isinstance(inp, bytearray):
        return bytes(inp)

    elif isinstance(inp, int):
        return inp.to_bytes(length, ('big' if bom == '>' else 'little'))

    elif isinstance(inp, str):
        return inp.encode('utf-8').ljust(length, b'\0')
