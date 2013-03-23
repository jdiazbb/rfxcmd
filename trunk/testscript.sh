#!/bin/sh

##############################################################################
#
# TESTSCRIPT.SH
#
# 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
#
# Regression test script for RFXCMD
#
#	Version history
#
# 	v0.3 22MAR13 
#		- Modified for rfxcmd v0.3x
#		- Added SqLite
#
##############################################################################

##############################################################################
#
# help()
#
##############################################################################

function help {

	echo "Options:"
	echo "-p = Printout test"
	echo "-c = CSV test"
	echo "-m = MySQL test"
	echo "-s = SqLite test"
	echo "-x = xPL test"
	echo "-h = Help, this text"
	exit 0
}

##############################################################################
#
# START
#
##############################################################################

echo "RFXCMD Regression test"

while getopts ":pcmsxh" opt; do
  case $opt in
    p)
      TEST="PRINTOUT"
      ;;
    c)
      TEST="CSV"
      ;;
    m)
      TEST="MYSQL"
      ;;
    s)
      TEST="SQLITE"
      ;;
    x)
      TEST="XPLITE"
      ;;
    h)
      help
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

if [[ $TEST == "" ]]; then
	echo "No test chosen"
fi

##############################################################################
#
# TEST: PRINTOUT
# Decode and print
#
##############################################################################

if [[ $TEST == "PRINTOUT" ]]; then

	echo "*** PRINTOUT TEST ***"
	echo "*** 0x10 ***"
	./rfxcmd.py -x 071000B7490A0160
	./rfxcmd.py -x 0710010041020150
	echo "*** 0x11 ***"
	./rfxcmd.py -x 0B110006007DB0C202010F70
	echo "*** 0x13 ***"
	./rfxcmd.py -x 09130003151555015E50
	echo "*** 0x15 ***"
	./rfxcmd.py -x 0B15000496FD480100046360
	echo "*** 0x19 ***"
	./rfxcmd.py -x 0919040600A21B010280
	./rfxcmd.py -x 091905021A6280010000
	echo "*** 0x20 ***"
	./rfxcmd.py -x 0820006CDED1DB0259
	./rfxcmd.py -x 0820062B7831800D59
	./rfxcmd.py -x 08200300346C000680
	echo "*** 0x30 ***"
	./rfxcmd.py -x 063000000F0D50
	./rfxcmd.py -x 06300200000B5A
	echo "*** 0x40 ***"
	./rfxcmd.py -x 09400001D05617148172
	./rfxcmd.py -x 09400002E75613120271
	echo "*** 0x42 ***"
	./rfxcmd.py -x 08420101019FAB0281
	echo "*** 0x50 ***"
	./rfxcmd.py -x 08500110000180BC69
	./rfxcmd.py -x 085002071F0100E489
	./rfxcmd.py -x 08500500050000E849
	./rfxcmd.py -x 085006003B0A00B459
	./rfxcmd.py -x 08500700BE0000DB79
	./rfxcmd.py -x 0850090797D0011889
	echo "*** 0x51 ***"
	./rfxcmd.py -x 085101027700360189
	./rfxcmd.py -x 0851029C6300290179
	echo "*** 0x52 ***"
	./rfxcmd.py -x 0A520106580100D9360159
	./rfxcmd.py -x 0A520200AC01004A440069
	./rfxcmd.py -x 0A5205D42F000082590379
	echo "*** 0x54 ***"
	./rfxcmd.py -x 0D540200910000D02C0103F20449
	echo "*** 0x55 ***"
	./rfxcmd.py -x 0B5501006D000001003FDE79
	./rfxcmd.py -x 0B55020096000000003B1869
	./rfxcmd.py -x 0B55059A6300000000004C89
	./rfxcmd.py -x 0850089D630000FF79
	echo "*** 0x56 ***"
	./rfxcmd.py -x 1056010040000000000000000000000049
	./rfxcmd.py -x 10560200A3000151000500040000000049
	./rfxcmd.py -x 105606A063000000000001FE0000000079
	echo "*** 0x57 ***"
	./rfxcmd.py -x 09570127CB0000E13A59
	./rfxcmd.py -x 09570200430000430059
	echo "*** 0x59 ***"
	./rfxcmd.py -x 0D5901015D0002001B0000000079
	echo "*** 0x5A ***"
	./rfxcmd.py -x 115A01071A7300000003F600000000350B89
	./rfxcmd.py -x 115A020284C2000000012100000F6984F669
	echo "*** 0x70 ***"
	./rfxcmd.py -x 077000003F06C950
	./rfxcmd.py -x 077002003F01F550
	./rfxcmd.py -x 077001003F001350
	echo "*** 0x71 ***"
	./rfxcmd.py -x 0A71003708F8008A646770
	echo "DONE"

fi

##############################################################################
#
# TEST: CSV PRINTOUT
# Decode and CSV print
#
##############################################################################

if [[ $TEST == "CSV" ]]; then

	echo "*** CSV TEST ***"
	echo "*** 0x10 ***"
	./rfxcmd.py -x 071000B7490A0160 -c
	./rfxcmd.py -x 0710010041020150 -c
	echo "*** 0x11 ***"
	./rfxcmd.py -x 0B110006007DB0C202010F70 -c
	echo "*** 0x13 ***"
	./rfxcmd.py -x 09130003151555015E50 -c
	echo "*** 0x15 ***"
	./rfxcmd.py -x 0B15000496FD480100046360 -c
	echo "*** 0x19 ***"
	./rfxcmd.py -x 0919040600A21B010280 -c
	./rfxcmd.py -x 091905021A6280010000 -c
	echo "*** 0x20 ***"
	./rfxcmd.py -x 0820006CDED1DB0259 -c
	./rfxcmd.py -x 0820062B7831800D59 -c
	./rfxcmd.py -x 08200300346C000680 -c
	echo "*** 0x30 ***"
	./rfxcmd.py -x 063000000F0D50 -c
	./rfxcmd.py -x 06300200000B5A -c
	echo "*** 0x40 ***"
	./rfxcmd.py -x 09400001D05617148172 -c
	./rfxcmd.py -x 09400002E75613120271 -c
	echo "*** 0x42 ***"
	./rfxcmd.py -x 08420101019FAB0281 -c
	echo "*** 0x50 ***"
	./rfxcmd.py -x 08500110000180BC69 -c
	./rfxcmd.py -x 085002071F0100E489 -c
	./rfxcmd.py -x 08500500050000E849 -c
	./rfxcmd.py -x 085006003B0A00B459 -c
	./rfxcmd.py -x 08500700BE0000DB79 -c
	./rfxcmd.py -x 0850089D630000FF79 -c
	./rfxcmd.py -x 0850090797D0011889 -c
	echo "*** 0x51 ***"
	./rfxcmd.py -x 085101027700360189 -c
	./rfxcmd.py -x 0851029C6300290179 -c
	echo "*** 0x52 ***"
	./rfxcmd.py -x 0A520106580100D9360159 -c
	./rfxcmd.py -x 0A520200AC01004A440069 -c
	./rfxcmd.py -x 0A5205D42F000082590379 -c
	echo "*** 0x54 ***"
	./rfxcmd.py -x 0D540200910000D02C0103F20449 -c
	echo "*** 0x55 ***"
	./rfxcmd.py -x 0B5501006D000001003FDE79 -c
	./rfxcmd.py -x 0B55020096000000003B1869 -c
	./rfxcmd.py -x 0B55059A6300000000004C89 -c
	echo "*** 0x56 ***"
	./rfxcmd.py -x 1056010040000000000000000000000049 -c
	./rfxcmd.py -x 10560200A3000151000500040000000049 -c
	./rfxcmd.py -x 105606A063000000000001FE0000000079 -c
	echo "*** 0x57 ***"
	./rfxcmd.py -x 09570127CB0000E13A59 -c
	./rfxcmd.py -x 09570200430000430059 -c
	echo "*** 0x59 ***"
	./rfxcmd.py -x 0D5901015D0002001B0000000079 -c
	echo "*** 0x5A ***"
	./rfxcmd.py -x 115A01071A7300000003F600000000350B89 -c
	./rfxcmd.py -x 115A020284C2000000012100000F6984F669 -c
	echo "*** 0x70 ***"
	./rfxcmd.py -x 077000003F06C950 -c
	./rfxcmd.py -x 077002003F01F550 -c
	./rfxcmd.py -x 077001003F001350 -c
	echo "*** 0x71 ***"
	./rfxcmd.py -x 0A71003708F8008A646770 -c
	echo "DONE"

fi

##############################################################################
#
# TEST: MYSQL
# Insert data to the MySQL database
#
##############################################################################

if [[ $TEST == "MYSQL" ]]; then

	echo "*** MYSQL TEST ***"
	echo "*** 0x10 ***"
	./rfxcmd.py -x 071000B7490A0160 -m
	./rfxcmd.py -x 0710010041020150 -m
	echo "*** 0x11 ***"
	./rfxcmd.py -x 0B110006007DB0C202010F70 -m
	echo "*** 0x13 ***"
	./rfxcmd.py -x 09130003151555015E50 -m
	echo "*** 0x15 ***"
	./rfxcmd.py -x 0B15000496FD480100046360 -m
	echo "*** 0x19 ***"
	./rfxcmd.py -x 0919040600A21B010280 -m
	./rfxcmd.py -x 091905021A6280010000 -m
	echo "*** 0x20 ***"
	./rfxcmd.py -x 0820006CDED1DB0259 -m
	./rfxcmd.py -x 0820062B7831800D59 -m
	./rfxcmd.py -x 08200300346C000680 -m
	echo "*** 0x30 ***"
	./rfxcmd.py -x 063000000F0D50 -m
	./rfxcmd.py -x 06300200000B5A -m
	echo "*** 0x40 ***"
	./rfxcmd.py -x 09400001D05617148172 -m
	./rfxcmd.py -x 09400002E75613120271 -m
	echo "*** 0x42 ***"
	./rfxcmd.py -x 08420101019FAB0281 -m
	echo "*** 0x50 ***"
	./rfxcmd.py -x 08500110000180BC69 -m
	./rfxcmd.py -x 085002071F0100E489 -m
	./rfxcmd.py -x 08500500050000E849 -m
	./rfxcmd.py -x 085006003B0A00B459 -m
	./rfxcmd.py -x 08500700BE0000DB79 -m
	./rfxcmd.py -x 0850089D630000FF79 -m
	./rfxcmd.py -x 0850090797D0011889 -m
	echo "*** 0x51 ***"
	./rfxcmd.py -x 085101027700360189 -m
	./rfxcmd.py -x 0851029C6300290179 -m
	echo "*** 0x52 ***"
	./rfxcmd.py -x 0A520106580100D9360159 -m
	./rfxcmd.py -x 0A520200AC01004A440069 -m
	./rfxcmd.py -x 0A5205D42F000082590379 -m
	echo "*** 0x54 ***"
	./rfxcmd.py -x 0D540200910000D02C0103F20449 -m
	echo "*** 0x55 ***"
	./rfxcmd.py -x 0B5501006D000001003FDE79 -m
	./rfxcmd.py -x 0B55020096000000003B1869 -m
	./rfxcmd.py -x 0B55059A6300000000004C89 -m
	echo "*** 0x56 ***"
	./rfxcmd.py -x 1056010040000000000000000000000049 -m
	./rfxcmd.py -x 10560200A3000151000500040000000049 -m
	./rfxcmd.py -x 105606A063000000000001FE0000000079 -m
	echo "*** 0x57 ***"
	./rfxcmd.py -x 09570127CB0000E13A59 -m
	./rfxcmd.py -x 09570200430000430059 -m
	echo "*** 0x59 ***"
	./rfxcmd.py -x 0D5901015D0002001B0000000079 -m
	echo "*** 0x5A ***"
	./rfxcmd.py -x 115A01071A7300000003F600000000350B89 -m
	./rfxcmd.py -x 115A020284C2000000012100000F6984F669 -m
	echo "*** 0x70 ***"
	./rfxcmd.py -x 077000003F06C950 -m
	./rfxcmd.py -x 077002003F01F550 -m
	./rfxcmd.py -x 077001003F001350 -m
	echo "*** 0x71 ***"
	./rfxcmd.py -x 0A71003708F8008A646770 -m
	echo "DONE"

fi

##############################################################################
#
# TEST: SQLITE
# Insert data to the SQLITE database
#
##############################################################################

if [[ $TEST == "SQLITE" ]]; then

	echo "*** SQLITE TEST ***"
	echo "*** 0x10 ***"
	./rfxcmd.py -x 071000B7490A0160 -s
	./rfxcmd.py -x 0710010041020150 -s
	echo "*** 0x11 ***"
	./rfxcmd.py -x 0B110006007DB0C202010F70 -s
	echo "*** 0x13 ***"
	./rfxcmd.py -x 09130003151555015E50 -s
	echo "*** 0x15 ***"
	./rfxcmd.py -x 0B15000496FD480100046360 -s
	echo "*** 0x19 ***"
	./rfxcmd.py -x 0919040600A21B010280 -s
	./rfxcmd.py -x 091905021A6280010000 -s
	echo "*** 0x20 ***"
	./rfxcmd.py -x 0820006CDED1DB0259 -s
	./rfxcmd.py -x 0820062B7831800D59 -s
	./rfxcmd.py -x 08200300346C000680 -s
	echo "*** 0x30 ***"
	./rfxcmd.py -x 063000000F0D50 -s
	./rfxcmd.py -x 06300200000B5A -s
	echo "*** 0x40 ***"
	./rfxcmd.py -x 09400001D05617148172 -s
	./rfxcmd.py -x 09400002E75613120271 -s
	echo "*** 0x42 ***"
	./rfxcmd.py -x 08420101019FAB0281 -s
	echo "*** 0x50 ***"
	./rfxcmd.py -x 08500110000180BC69 -s
	./rfxcmd.py -x 085002071F0100E489 -s
	./rfxcmd.py -x 08500500050000E849 -s
	./rfxcmd.py -x 085006003B0A00B459 -s
	./rfxcmd.py -x 08500700BE0000DB79 -s
	./rfxcmd.py -x 0850089D630000FF79 -s
	./rfxcmd.py -x 0850090797D0011889 -s
	echo "*** 0x51 ***"
	./rfxcmd.py -x 085101027700360189 -s
	./rfxcmd.py -x 0851029C6300290179 -s
	echo "*** 0x52 ***"
	./rfxcmd.py -x 0A520106580100D9360159 -s
	./rfxcmd.py -x 0A520200AC01004A440069 -s
	./rfxcmd.py -x 0A5205D42F000082590379 -s
	echo "*** 0x54 ***"
	./rfxcmd.py -x 0D540200910000D02C0103F20449 -s
	echo "*** 0x55 ***"
	./rfxcmd.py -x 0B5501006D000001003FDE79 -s
	./rfxcmd.py -x 0B55020096000000003B1869 -s
	./rfxcmd.py -x 0B55059A6300000000004C89 -s
	echo "*** 0x56 ***"
	./rfxcmd.py -x 1056010040000000000000000000000049 -s
	./rfxcmd.py -x 10560200A3000151000500040000000049 -s
	./rfxcmd.py -x 105606A063000000000001FE0000000079 -s
	echo "*** 0x57 ***"
	./rfxcmd.py -x 09570127CB0000E13A59 -s
	./rfxcmd.py -x 09570200430000430059 -s
	echo "*** 0x59 ***"
	./rfxcmd.py -x 0D5901015D0002001B0000000079 -s
	echo "*** 0x5A ***"
	./rfxcmd.py -x 115A01071A7300000003F600000000350B89 -s
	./rfxcmd.py -x 115A020284C2000000012100000F6984F669 -s
	echo "*** 0x70 ***"
	./rfxcmd.py -x 077000003F06C950 -s
	./rfxcmd.py -x 077002003F01F550 -s
	./rfxcmd.py -x 077001003F001350 -s
	echo "*** 0x71 ***"
	./rfxcmd.py -x 0A71003708F8008A646770 -s
	echo "DONE"

fi

