# BCFSTM-BCFWAV-Converter
A tool to convert between the BFSTM, BCSTM, BFSTP, BFWAV, and BCWAV formats.
Special thanks to Gota7 for explanation of sample data structure in WAV.

## Usage:
`main [option...] input`

### Options:
- `-format [dstFmt]` destination format
- `-bom [bom]` endianness (Optional)

### Supported dest formats:
- FSTM
- CSTM
- FSTP
- FWAV
- CWAV

### bom:
- 0 - Big Endian (Wii U)
- 1 - Little Endian (3DS/Switch)
