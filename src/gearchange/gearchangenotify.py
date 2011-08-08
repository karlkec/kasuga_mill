#!/usr/bin/python
""" This is a program to prompt the operator to change the gear settings.
	Copyright (C) 2011 Karl Cunningham

	This program is free software; you can redistribute it and/or modify it
	under the terms of the GNU General Public License as published by the Free
	Software Foundation; either version 3 of the License, or any later version.

	This program is distributed in the hope that it will be useful, but WITHOUT
	ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
	FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along
	with this program; if not, see <http://www.gnu.org/licenses/>.
"""

""" Notify Type == 1 -> Prompts the operator to change the belt and gear settings.

    Three additional command-line arguments are required, The first is an index
    to the belt and gear to be propted for.  This command-line argument must be
    a number, 1-10. This range is from the lowest gear to the highest gear (and
    belt setting). Settings 1-5 are in LOW range, and 6-10 are HIGH range.

    The second and third arguments are the minimum and maximum spindle speed for
    this gear. These are used to create the text.

    Two buttons are given at the bottom of the prompt: PROCEED and ABORT.
	
    This type returns 0 if the operator clicks PROCEED, or 255 if the
    command-line argument is invalid, the operator clicks ABORT, closes the
    window, or presses ESC.

    The IMGPATH variable below should be set to the path to (or possibly a
    symlink to) the accompanying images which show the operator the belt and gear
    lever positions. There is on image per gear setting.

    Notify Type == 2 -> Displays a limited speed notification. This is a
    text-based notification telling the operator that the spindle speed will be
    limited to XXX RPM and that the motor will be run at a speed limit (low or
    high). Three additional command-line arguments are required, the desires
    spindle speed, the minimum spindle speed for this gear, and the maximum
    spindle speed for this gear. Only one button is presented -- OK -- which
    returns with a code of 0.

    Notify Type == 3 -> Displays a notification that the machine cannot
    accommodate the desired spindle speed. The desired speed and the closest
    machine speed to that are presented, and the operator is allowed two
    buttons.  The first, USE CLOSEST, will return with a code of 0. The other,
    ABORT, will return with a code of 254. This type requires two additional
    command-line arguments, the desired spindle speed, and the closest machine
    speed.

    Notify Type == 4 -> Displays a notification that the desired spindle speed
    is not far outside the limits of the current gear, and asks the operator
    whether to switch gears or use the current gear. It requires two additional
    command-line arguments, the desired speed and the closest speed with the
    current gear. It returns 0 if the operator wants to change gears, and 1 if
    the operator wants to keep the current gear.
"""

from Tkinter import *
import sys
import re

# Path to image files
IMGPATH = "images/"

EXIT_OK = 0
EXIT_ERROR = 255
EXIT_ABORT = 254
EXIT_USETHIS = 0
EXIT_CHANGE = 1
EXIT_CLOSEST = 0

retval = EXIT_OK

class Type1_notification:
    """ Displays the message to the operator
    """
    def __init__(self,master,ratio,desiredspeed,minspeed,maxspeed,title=None):
        self.master = master

        if(title):
            self.master.title(title)

        # Handle clicking the X in the corner
        self.master.protocol("WM_DELETE_WINDOW", self.abort)

		# Decode the ratio into belt and gear values. These have become less straightforward
        #  so we play some arithmetic games here
        self.belt = 4 - ((ratio - 1) % 5)
        self.gear = (ratio - 1) // 5

        if(self.belt == 0):
            # Highest Speed of the belt positions
            self.beltimg = "belt1.gif"
            self.belttxt = "Change the Belt to the TOP Position"
        elif(self.belt == 1):
            self.beltimg = "belt2.gif"
            self.belttxt = "Change the Belt to the SECOND Position"
        elif(self.belt == 2):
            self.beltimg = "belt3.gif"
            self.belttxt = "Change the Belt to the MIDDLE Position"
        elif(self.belt == 3):
            self.beltimg = "belt4.gif"
            self.belttxt = "Change the Belt to the FOURTH Position"
        else: # self.belt == 4
            # Lowest Speed of the belt positions
            self.beltimg = "belt5.gif"
            self.belttxt = "Change the Belt to the BOTTOM Position"

        self.beltimg = IMGPATH + self.beltimg

        if(self.gear == 0):
            self.gearimg = "gearL.gif"
            self.geartxt = "Set the Gear Lever to LOW"
        else:
            self.gearimg = "gearH.gif"
            self.geartxt = "Set the Gear Lever to HIGH"

        # Prepend the image path and set up the dialog
        self.gearimg = IMGPATH + self.gearimg
        self.inittext = "When the Spindle is Stopped\n"
        self.dialog = self.inittext+self.belttxt+"\n"+"and "+ self.geartxt+"\n"

        self.frame1 = Frame(master)
        self.frame1.pack()

        self.beltpic = PhotoImage(file=self.beltimg)
        self.picture1 = Label(self.frame1, image=self.beltpic)
        self.picture1.pack()

        self.gearpic = PhotoImage(file=self.gearimg)
        self.picture2 = Label(self.frame1, image=self.gearpic)
        self.picture2.pack()

        self.msg1 = Label(self.frame1,text=self.dialog,fg="red")
        self.msg1.pack()

        self.speedtext1 = "Desired Spindle Speed is %d RPM\n" % (desiredspeed)
        self.speedtext2 = "Speed range for this gear is %d to %d RPM" % (minspeed,maxspeed)
        self.speedtext = self.speedtext1 + self.speedtext2
        self.msg2 = Label(self.frame1,text=self.speedtext)
        self.msg2.pack()

        self.finaltext = "Click PROCEED when Done or ABORT to Stop"
        self.msg3 = Label(self.frame1,text=self.finaltext,fg="red")
        self.msg3.pack()

        self.frame2 = Frame(self.frame1)
        self.frame2.pack(pady=10)

        self.abort_button = Button(self.frame2,text="ABORT",command=self.abort)
        self.abort_button.pack(side=LEFT)
        self.abort_button.bind("<Return>",self.abort)
        self.abort_button.bind("<Escape>",self.abort)

        self.cont_button = Button(self.frame2,text="PROCEED",command=self.ok)
        self.cont_button.pack(side=LEFT)
        self.cont_button.bind("<Return>",self.ok)
        self.cont_button.bind("<Escape>",self.abort)
        self.cont_button.focus_set()

    def abort(self,t=0):
        global retval
        retval = EXIT_ABORT
        self.frame1.quit()

    def ok(self,t=0):
        global retval
        retval = EXIT_OK
        self.frame1.quit()

    def center(self):
        """ Centers the window """
        w = 320
        h = 370
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry("%dx%d+%d+%d" % (w,h,(sw-w)/2,(sh-h)/2))

class Type2_notification:
    """ Displays a message to the operator about the fact the desired spindle speed
        is outside the range for the selected gear, and the motor will be running at
        its speed limit.
    """
    def __init__(self,master,desiredspeed,minspeed,maxspeed,title=None):
        self.master = master

        if(title):
            self.master.title(title)

        # Handle clicking the X in the corner
        self.master.protocol("WM_DELETE_WINDOW", self.ok)

        # Decide which limit we are up against
        if(desiredspeed < minspeed):
            whichlimit = "Minimum"
            spindlespeed = minspeed
        else:
            whichlimit = "Maximum"
            spindlespeed = maxspeed
        self.lines = []
        self.lines.append("Caution -- The Desired Spindle Speed (%d RPM)\n" % (desiredspeed))
        self.lines.append("is Outside the Speed Range for this\n")
        self.lines.append("Gear (%d to %d RPM). The Spindle Will Run\n" % (minspeed,maxspeed))
        self.lines.append("at %d RPM and the Motor Will Run\n" % spindlespeed)
        self.lines.append("at %s Speed During this Operation\n" % whichlimit)

        self.frame1 = Frame(master)
        self.frame1.pack()

        self.msgtext = ''.join(self.lines)
        self.msg1 = Label(self.frame1,text=self.msgtext)
        self.msg1.pack()

        self.frame2 = Frame(self.frame1)
        self.frame2.pack()

        self.ok_button = Button(self.frame2,text="OK",command=self.ok,
                width=4,height=2)
        self.ok_button.pack(side=LEFT)
        self.ok_button.bind("<Return>",self.ok)
        self.ok_button.bind("<Escape>",self.ok)
        self.ok_button.focus_set()

    def ok(self,t=0):
        global retval
        retval = EXIT_OK
        self.frame1.quit()

    def center(self):
        """ Centers the window """
        w = 320
        h = 130
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry("%dx%d+%d+%d" % (w,h,(sw-w)/2,(sh-h)/2))

class Type3_speed_notification:
    """ Displays a message to the operator about the fact the desired spindle speed
        is outside the range for the machine. Asks the operator to decide
        whether to use the closest speed or abort the program.
    """
    def __init__(self,master,desiredspeed,closest,title=None):
        self.master = master

        if(title):
            self.master.title(title)

        # Handle clicking the X in the corner
        self.master.protocol("WM_DELETE_WINDOW", self.closest)

        # Decide which limit we're fighting
        if(desiredspeed < closest):
            whichlimit = "Minimum"
        else:
            whichlimit = "Maximum"

        self.lines = []
        self.lines.append("The Desired Spindle Speed (%d RPM)\n" % (desiredspeed))
        self.lines.append("is Outside the Speed Range for the\n")
        self.lines.append("Machine (%d RPM). Click USE CLOSEST to continue\n" % (closest))
        self.lines.append("at %d RPM, or ABORT to Stop the Program\n" % (closest))

        self.frame1 = Frame(master)
        self.frame1.pack()

        self.msgtext = ''.join(self.lines)
        self.msg1 = Label(self.frame1,text=self.msgtext)
        self.msg1.pack()

        self.frame2 = Frame(self.frame1)
        self.frame2.pack()

        self.closest_button = Button(self.frame2,text="USE CLOSEST",command=self.closest,
                width=10,height=2)
        self.closest_button.pack(side=LEFT)
        self.closest_button.bind("<Return>",self.closest)
        self.closest_button.bind("<Escape>",self.abort)
        self.closest_button.focus_set()

        self.spacer = Label(self.frame2,text="",width=2)
        self.spacer.pack(side=LEFT)

        self.abort_button = Button(self.frame2,text="ABORT",command=self.abort,
                width=4,height=2)
        self.abort_button.pack(side=LEFT)
        self.abort_button.bind("<Return>",self.abort)
        self.abort_button.bind("<Escape>",self.abort)

    def abort(self,t=0):
        global retval
        retval = EXIT_ABORT
        self.frame1.quit()

    def closest(self,t=0):
        global retval
        retval = EXIT_CLOSEST
        self.frame1.quit()

    def center(self):
        """ Centers the window """
        w = 340
        h = 130
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry("%dx%d+%d+%d" % (w,h,(sw-w)/2,(sh-h)/2))

class Type4_speed_notification:
    """ Displays a message to the operator about the fact the desired spindle speed
        is outside the range for the selected gear, and the motor will be running at
        its speed limit.
    """
    def __init__(self,master,desiredspeed,closest,title=None):
        self.master = master

        if(title):
            self.master.title(title)

        # Handle clicking the X in the corner
        self.master.protocol("WM_DELETE_WINDOW", self.usethis)

        self.lines = []
        self.lines.append("The Desired Spindle Speed of %d RPM\n" % (desiredspeed))
        self.lines.append("is Outside the Limit for this Gear (%d RPM).\n" % (closest))
        self.lines.append("Click USE THIS GEAR to Use %d RPM,\n" % (closest))
        self.lines.append("or Click CHANGE GEAR to Use the Right Gear\n")

        self.frame1 = Frame(master)
        self.frame1.pack()

        self.msgtext = ''.join(self.lines)
        self.msg1 = Label(self.frame1,text=self.msgtext)
        self.msg1.pack()

        self.frame2 = Frame(self.frame1)
        self.frame2.pack()

        self.usethis_button = Button(self.frame2,text="USE THIS GEAR",command=self.usethis,
                width=13,height=2)
        self.usethis_button.pack(side=LEFT)
        self.usethis_button.bind("<Return>",self.usethis)
        self.usethis_button.bind("<Escape>",self.usethis)
        self.usethis_button.focus_set()

        self.spacer = Label(self.frame2,text="",width=2)
        self.spacer.pack(side=LEFT)

        self.change_button = Button(self.frame2,text="CHANGE GEAR",command=self.change,
                width=10,height=2)
        self.change_button.pack(side=LEFT)
        self.change_button.bind("<Return>",self.change)
        self.change_button.bind("<Escape>",self.change)

    def usethis(self,t=0):
        global retval
        retval = EXIT_USETHIS
        self.frame1.quit()

    def change(self,t=0):
        global retval
        retval = EXIT_CHANGE
        self.frame1.quit()

    def center(self):
        """ Centers the window """
        w = 320
        h = 130
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry("%dx%d+%d+%d" % (w,h,(sw-w)/2,(sh-h)/2))

class Type5_speed_notification:
    """ Displays a message to the operator that the values of some of the pins and/or
        parameters are out of range.
    """
    def __init__(self,names,title=None):
        self.master = master

        if(title):
            self.master.title(title)

        # Handle clicking the X in the corner
        self.master.protocol("WM_DELETE_WINDOW", self.closest)

        self.lines = []
        self.lines.append("The Following Pins/Parameters are Invalid\n")
        self.lines.append("Please Correct and Restart EMC2")

        self.frame1 = Frame(master)
        self.frame1.pack()

        self.msgtext = ''.join(self.lines)
        self.msg1 = Label(self.frame1,text=self.msgtext)
        self.msg1.pack()

        self.frame2 = Frame(self.frame1)
        self.frame2.pack()

        self.closest_button = Button(self.frame2,text="OK",command=self.ok,
                width=10,height=2)
        self.closest_button.pack(side=LEFT)
        self.closest_button.bind("<Return>",self.ok)
        self.closest_button.bind("<Escape>",self.ok)
        self.closest_button.focus_set()

    def ok(self,t=0):
        global retval
        retval = EXIT_ABORT
        self.frame1.quit()

    def center(self):
        """ Centers the window """
        w = 340
        h = 130
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry("%dx%d+%d+%d" % (w,h,(sw-w)/2,(sh-h)/2))

def parse_cli(notifytype):
    if(notifytype == 1):
        if(len(sys.argv) < 5):
            sys.stderr.write( "Not enough command-line arguments passed "
                    "to %s\n"%sys.argv[0])
            sys.stderr.write( "   First argument must be an integer with the type of "
                    "notification required\n")
            sys.stderr.write( "   Second argument must be the gear ratio desired (1 through "
                    "10)\n")
            sys.stderr.write( "   Third argument must be a number with the desired spindle speed\n")
            sys.stderr.write( "   Fourth argument must be a number with the minimum "
                    "spindle speed for this gear\n")
            sys.stderr.write( "   Fifth argument must be a number with the maximum "
                    "spindle speed for this gear\n")
            sys.exit(EXIT_ERROR)

        try:
            # Convert the min and max spindle speeds to numbers.
            gearno = int(sys.argv[2])
            desiredspeed = float(sys.argv[3])
            minspeed = float(sys.argv[4])
            maxspeed = float(sys.argv[5])
        except ValueError,OverflowError:
            sys.stderr.write( "Invalid min or max speed passed to %s\n" % sys.argv[0],"Must "
                    "be numbers\n")
            sys.exit(EXIT_ERROR)
        return(gearno,desiredspeed,minspeed,maxspeed)
    elif(notifytype == 2):
        if(len(sys.argv) < 5):
            sys.stderr.write( "Not enough command-line arguments passed "
                    "to %s\n" % sys.argv[0])
            sys.stderr.write( "   First argument must be an integer with the type of "
                    "notification required\n")
            sys.stderr.write( "   Second  argument must be a number with the desired "
                    "spindle speed for this gear\n")
            sys.stderr.write( "   Third argument must be a number with the minimum "
                    "spindle speed for this gear\n")
            sys.stderr.write( "   Fourth argument must be a number with the maximum "
                    "spindle speed for this gear\n")
            sys.exit(EXIT_ERROR)
    
        try:
            # Convert the min and max spindle speeds to numbers.
            desiredspeed = float(sys.argv[2])
            minspeed = float(sys.argv[3])
            maxspeed = float(sys.argv[4])
        except ValueError,OverflowError:
            sys.stderr.write( "Invalid desired, min, or max speed passed "
                            "to %s\n" % sys.argv[0],"Must be numbers\n")
            sys.exit(EXIT_ERROR)
        return(desiredspeed,minspeed,maxspeed)

    elif(notifytype == 3):
        if(len(sys.argv) < 5):
            sys.stderr.write( "Not enough command-line arguments passed "
                    "to %s\n" % sys.argv[0])
            sys.stderr.write( "   First argument must be an integer with the type of "
                    "notification required\n")
            sys.stderr.write( "   Second  argument must be a number with the desired "
                    "spindle speed for this gear\n")
            sys.stderr.write( "   Third argument must be a number with the machine's "
                    "closest spindle speed\n")
            sys.exit(EXIT_ERROR)
    
        try:
            # Convert the min and max spindle speeds to numbers.
            desiredspeed = float(sys.argv[2])
            closest = float(sys.argv[3])
        except ValueError,OverflowError:
            sys.stderr.write( "Invalid desired or closest speed passed "
                            "to %s\n" % sys.argv[0],"Must be numbers\n")
            sys.exit(EXIT_ERROR)
        return(desiredspeed,closest)

    elif(notifytype == 4):
        if(len(sys.argv) < 5):
            sys.stderr.write( "Not enough command-line arguments passed "
                    "to %s\n" % sys.argv[0])
            sys.stderr.write( "   First argument must be an integer with the type of "
                    "notification required\n")
            sys.stderr.write( "   Second  argument must be a number with the desired "
                    "spindle speed for this gear\n")
            sys.stderr.write( "   Third argument must be a number with the closest "
                    "spindle speed for this gear\n")
            sys.exit(EXIT_ERROR)
    
        try:
            # Convert the min and max spindle speeds to numbers.
            desiredspeed = float(sys.argv[2])
            closest = float(sys.argv[3])
        except ValueError,OverflowError:
            sys.stderr.write( "Invalid desired or closest speed passed "
                            "to %s\n" % sys.argv[0],"Must be numbers\n")
            sys.exit(EXIT_ERROR)
        return(desiredspeed,closest)

    elif(notifytype == 5):
        if(len(sys.argv) < 3):
            sys.stderr.write("Not enough command-line arguments passed "
                    "to %s\n" % sys.argv[0])
            sys.stderr.write("   First argument must be an integer with the type of "
                    "notification required\n")
            sys.stderr.write("   Second  argument must be a list of bad pins/parameters\n")
            sys.exit(EXIT_ERROR)
    
        try:
            # Convert the comma-separated string of bad pins to a list
            pinlist = sys.argv[3].split(',')
        except ValueError,OverflowError:
            sys.stderr.write( "Invalid list of bad pins/parameters\n")
            sys.exit(EXIT_ERROR)
        return(pinlist)


################################ MAIN PROGRAM ##########################
def main():
    # First Command-line Argument is the gear ratio desired, 1-10
    if(len(sys.argv) < 2):
        sys.stderr.write( "Not enough command-line arguments passed to %s\n" % sys.argv[0])
        sys.stderr.write( "   First argument must be an integer with the type of "
                "notification required\n")
        sys.exit(EXIT_ERROR)

    try:
		# Convert the ratio to an integer. This will filter out lots of possible bogus stuff
        notifytype = int(sys.argv[1])
    except ValueError,OverflowError:
        sys.stderr.write("Invalid First Argument passwd to %s\n" % sys.argv[0]," Must "
                "be an Integer\n")
        sys.exit(EXIT_ERROR)

    if(notifytype == 1):
        # The third and fourth arguments are the min and max spindle speed for
        # this gear 
        (gearno,desiredspeed,minspeed,maxspeed) = parse_cli(1)
        # Put up the message
        root = Tk()
        dlg = Type1_notification(root,gearno,desiredspeed,minspeed,maxspeed,"Gear Change")
        dlg.center()
        root.mainloop()
    elif(notifytype == 2):
        # The third argument is the desired spindle speed, and the fourth and
        # fifth arguments are the min and max spindle speed for this gear 
        (desiredspeed,minspeed,maxspeed) = parse_cli(2)
        # Put up the message
        root = Tk()
        dlg = Type2_notification(root,desiredspeed,minspeed,maxspeed,"Speed Limit")
        dlg.center()
        root.mainloop()
    elif(notifytype == 3):
        # The third argument is the desired spindle speed, and the fourth and
        # fifth arguments are the min and max spindle speed for this gear 
        (desiredspeed,closest) = parse_cli(3)
        # Put up the message
        root = Tk()
        dlg = Type3_speed_notification(root,desiredspeed,closest,"Speed Limit")
        dlg.center()
        root.mainloop()
    elif(notifytype == 4):
        # The third argument is the desired spindle speed, and the fourth and
        # fifth arguments are the min and max spindle speed for this gear 
        (desiredspeed,closest) = parse_cli(4)
        # Put up the message
        root = Tk()
        dlg = Type4_speed_notification(root,desiredspeed,closest,"Speed Limit")
        dlg.center()
        root.mainloop()
    elif(notifytype == 5):
        # The third argument is the desired spindle speed, and the fourth and
        # fifth arguments are the min and max spindle speed for this gear 
        badpins = parse_cli(4)
        # Put up the message
        root = Tk()
        dlg = Type5_speed_notification(root,badpins,"Invalid Pins/Parameters")
        dlg.center()
        root.mainloop()

    #print "retval = ",retval
    return retval

if __name__ == '__main__':
    mainret = main()
    sys.exit(mainret)
    
