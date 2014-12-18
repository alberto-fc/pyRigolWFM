#! /usr/bin/env python

#from __future__ import print_function, with_statement
import argparse
import collections
import sys

import wfm

if __name__ == "__main__":
  import argparse
  import pprint

  parser = argparse.ArgumentParser(description='Rigol DS1000Z series WFM file reader')
  parser.add_argument('action', choices=['info', 'csv', 'plot', 'json', 'vcd', 'ols'], help="Action")
  parser.add_argument('infile', type=argparse.FileType('rb'))
  parser.add_argument('--forgiving', action='store_false', help="Lazier file parsing")
  
  args = parser.parse_args()
   
  try:
    with args.infile as f:
      scopeData = wfm.parseRigolWFM(f, args.forgiving)
  except wfm.FormatError as e:
    sys.exit()
  
  if args.action == "plot":
    import numpy as np
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import scipy
    import scipy.fftpack
    
    mpl.rcParams['agg.path.chunksize'] = 100000
    
    plt.subplot(211)
    plt.plot(scopeData["time"], scopeData["channels"][0]['data'])
    plt.grid()
    plt.ylabel("Voltage [V]")
    
    plt.title("Waveform")
    plt.xlabel("Time [s]")
    
    plt.subplot(212)
    signal = np.array(scopeData["channels"][0]['data'])
    fft = np.abs(np.fft.fftshift(scipy.fft(signal)))
    freqs = np.fft.fftshift(scipy.fftpack.fftfreq(signal.size, scopeData["timeDiv"]))
    plt.plot(freqs, 20 * np.log10(fft))
      
    plt.grid()
    plt.title("FFT")
    plt.ylabel("Magnitude [dB]")
    plt.xlabel("Frequency [Hz]")
      
    plt.show()
    
  #scopeDataDsc = wfm.describeScopeData(scopeData)
  
  #if args.action == "info":
  #  print(scopeDataDsc)