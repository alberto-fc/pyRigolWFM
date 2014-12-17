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
  
  #scopeDataDsc = wfm.describeScopeData(scopeData)
  
  #if args.action == "info":
  #  print(scopeDataDsc)