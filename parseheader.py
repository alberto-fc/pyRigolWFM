#! /usr/bin/env python

import sys
from struct import *

def printf(str, *args):
    print str % args, 

def RunMain():
	
	f = open("header.wfm", "rb")
	strPack = sys.argv[1];
	packSize = calcsize(strPack);
	offset = int(sys.argv[3]);
	cycles = int(sys.argv[2]);
	printf("Procesando %s size %i\n", strPack, packSize);
	point = 0;
	buf = f.read(offset);
	point += len(buf);
	
	while True:
			buf = f.read(packSize);
					
			if len(buf) < packSize:
				break
			
			if cycles <= 0:
				break
			
			cycles -= 1
			
			printf("%.4X ", point);
			point += len(buf);
			
			for ch in buf:
				printf("[%.2X] ", ord(ch));

			num = unpack(strPack, buf)[0];

			#printf(" %12.i %10.X\n", num, num);
			print num;
			printf(" %f\n", num);
	
	
	f.close()

if __name__ == '__main__':
	print "AJA"
	
	try:
		RunMain()
	except KeyboardInterrupt:
		print "Saliendo!"
		sys.exit
		#raise
	except:
		raise