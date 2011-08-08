#!/usr/bin/python

""" gearchange is a tool to modify gcode for the Kasuga mill. It modified spindle
    commands and outputs more gcode. See below. In the description that follows, 
	the word "gear" is used to mean both belt and gear settings.

    Copyright (C) 2011 Karl Cunningham
    This program is free software; you can redistribute it and/or modify it under
    the terms of the GNU General Public License as published by the Free Software
    Foundation; either version 3 of the License, or any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
    PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, see <http://www.gnu.org/licenses/>.
"""

""" 
	This is a program written to support the Kasuga mill. It is desiged to act
	as a filter to batch-process a G-code file, to intercept Sxxx (spindle
	speed) commands and command a gear change as needed. Each time a gear
	change is needed an M5 command is inserted to stop the spindle, followed by
	a M100 PXX QXX to prompt the user to change gears, followed by the original
	SXXX to set the new spindle speed, followed by an M3 or M4 (depending on
	spindle direction).

    The G-code file is read from standard input and the (possibly) modified file
    is written to standard output.
    
	Gear ratios are read from the ini file in use by the axis component of
	emc2. The ratio is accomplished in two stages, a five-step pully
	arrangement on the motor, and a two-speed gear change in the mill head. For our 
	purposes, we use a single index into the array of gear ratios, and a single
	gear number to indicate which gear to use.

    The spindle speed nameplate on the mill reads thus for 60Hz to the motor:
       Belt Pos:     1       2       3       4       5
       Low Range    3000    2300    1600    1000    530
       High Range    450     350     245     150     75

	In evaluating the need for a gear change, preference is given to
	maintaining the same gear setting and merely changeing the motor frequency.
	Similarly, if a gear or belt change is needed, preference is given to
	operating the motor as close to its rated 60Hz as possible.

	The motor can operate over an RPM range of approximately 1300 to 2500 RPM,
	with nominal being 60Hz, or 1800RPM. These numbers ignore synchronization
	slippage which varies with load on the motor. In calcuations below, it is
	assumed to be about 3%.  Belt slippage is ignored completely.

	In all cases, the first Sxxx command found in the G-code file will result
	in a gear change to the gear needed for that speed. It is assumed that the
	gear at startup is incorrect, and will have to be changed. If that is not
	the case, the operator can simply acknowledge the gear change request and
	move on quickly.

	The current spindle speed, is maintained saved though the duration of the
	program run. The algorithm to look for a new gear first checks to see if
	the new speed would put the motor out of its speed range using the current
	gear setting. If it does not, the gear setting is maintained and the new
	spindle speed is inserted into the output stream.

	If the motor cannot be commanded to go to the required speed with the
	current gear setting, a new gear setting is chosen. This is done by finding
	which of the ratios will result in a motor speed closest to its nameplate
	speed.

	If the desired speed cannot be reached in any gear, a warning box is
	presented telling the user of the problem and at which line in the original
	G-code program the problem occurred.  If the program completes
	successfully, a notification is presented, telling the user of the number
	of speed changes, whether they involve a gear change, and which gear it
	will be.
"""

import sys
import re

MOTOR_NOM = 1750 # RPM
MOTOR_MAX = MOTOR_NOM * 1.388  # RPM
MOTOR_MIN = MOTOR_NOM * 0.720  # RPM

# Pattern to separate file into words
pattern_main = re.compile('([(!;].*|\s+|[a-zA-Z0-9_:](?:[+-])?\d*(?:\.\d*)?|\w\#\d+|\(.*?\)|\#\d+\=(?:[+-])?\d*(?:\.\d*)?)')

def find_gear(newsspeed, oldsspeed, oldgear):
    """ Determines a new gear setting. Does this by first checking the old
        gear ratio to see if the new requested spindle speed is ok for that
        gear. If it is, the old gear is returned.
        If not, or if there was no old gear, checks to which gear puts the motor closest 
        to its nominal RPM. Returns that gear if the motor is within its range. Otherwise,
        returns -1 (no gear).
    """
    if(oldgear >= 0):
        oldmotor = oldsspeed * ratios[oldgear]
        if(newsspeed * ratios[oldgear] >= MOTOR_MIN or newsspeed * ratios[oldgear] <= MOTOR_MAX):
            # We can use the current gear
            return oldgear

    # Find optimum gear. Check motor speed for each gear and find the one closest to MOTOR_NOM
    speedratio = 1e9  # very large number
    for gearno in range(len(ratios)):
        trialratio = (newsspeed * ratios[gearno]) / MOTOR_NOM
        if(trialratio < 1):
            trialratio = 1 / trialratio
        if(trialratio < speedratio):
            speedratio = trialratio
            newgear = gearno
    # We've found the gear with the ratio closest to running the motor at nominal speed.
    # Check that it's within the motor limits
    newmotorspeed = newsspeed / ratio[newgear]
    if(newmotorspeed < MOTOR_MIN or newmotorspeed > MOTOR_MAX):
        return -1
    else:
        return newgear

def writegearchange(newgear,newsspeed,spindledir):
    # Writes the commands to go to the new gear and motor speed
    newmotorspeed = newsspeed * ratios[newgear]
    print "M5\n"
    # The M100 command's gear numbers are 1-based, not 0-based
    print "M100 P%02d\n" % newgear + 1
    print "S%04d\n" % newmotorspeed
    print "M101\n"
    print "%s\n" % spindledir

def writemotorspeed(gear,newsspeed):
    # Writes a spindle speed change and prompt to acknowledge new speed. Write to stdout
    newmotorspeed = newsspeed * ratios[gear]
    print "S%04d\n" % newmotorspeed 
    print "M101\n"

############################# MAIN PROGRAM #############################

# Get the name of the INI file used by emc2
inifile = getinifile()

if(len(inifile)):
	inidata = parseinifile(inifile)

if(checkgeardata(inidata) < 0):
	# Bad gear change data from ini file

# Start reading stdin. For each line of g-code, keep track of the spindle rotation direction
#    (and whether it's on)
oldspeed = 0  # Spindle Speed
spdir = 'M5'  # Spindle direction (default == stopped)
m100_com = False
gear = -1 # No gear
for line in sys.stdin:
    line.rstrip()
    words = pattern_main.findall()
    added = ''
    for word in words:
        if(word[0]  == 'S' or word[0] == 's'):
            curspeed = eval(word[1:])
            oldgear = gear
            gear = findgear(curspeed,oldspeed,oldgear)
            oldspeed = curspeed
            if(gear < 0):
                # No gear change
                writemotorspeed(oldgear,newsspeed)
                gear = oldgear
            else:
                writegearchange(gear,newsspeed,spdir)
            savegearchange(oldgear,gear,
            continue
        elif((word[0] == "M" or word[0] == "m") and eval(word[1:]) in [3,6]):
            # Find a spindle direction or stop command, M3, M4 or M5
            spdir = word
            continue
        elif(word == "M100" or word == "m100"):
            # Ignore this one, from a previous run. Set the flag to see if this is followed by
            #  a PXXX command (which is should be). We'll swallow that one too
            m100_com = True
            continue
        elif(word == "M101" or word == "m101"):
            # Ignore this one, from a previous run.
            continue
        elif(word[0] == "P" or word[0] == "p" and m100_com):
            # Swallow the command and end the m100_com state
            m100_com = False
            continue

        # Now write what we have since we didn't find anything interesting
        print word+"\n"

