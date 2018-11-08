# BCFSTM-BCFWAV-Converter
A tool to convert between the BFSTM, BCSTM, BFSTP, BFWAV, and BCWAV formats.  
Special thanks to Gota7 for explanation of sample data structure in WAV.  
  
## Usage:
<code>main [option...] input</code>  
  
### Options:
<ul>
<li><code>-format [dstFmt]</code>  destination format</li>
<li><code>-bom [bom]</code>        endiannes (Optional)</li>
</ul>
  
### Supported dest formats:
<ul>
<li>FSTM</li>
<li>CSTM</li>
<li>FSTP</li>
<li>FWAV</li>
<li>CWAV</li>
</ul>
  
### bom:
<ul>
<li>0 - Big Endain (Wii U)</li>
<li>1 - Little Endian (3DS/Switch)</li>
</ul>
