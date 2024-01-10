# City of Heroes - Combat Parser
A Very basic Python-based parsing program for City of Heroes. This will read chat logs to parse combat data both in realtime and for previous encounters.

This is currently in **ALPHA** - expect code to be buggy and possible inaccuracies in the data.


### What it can do

- Log outgoing damage from yourself and from your pets
    - Calculate overall DPS
    - Show damage data for individual abilities, procs, and their damage types
    - Calculate the average damage per hit, per ability
- Log hit accuracy
- Automatically split logs into combat sessions
    - A Sesison starts when you activate an ability and finishes 15 seconds after no further damage was done
    - Session duration is measured from the first damaging ability to the last (to the nearest second) 

## Installation and Operation

1. In the Releases, download the  `CoH_Parser.exe` file, ignore the rest as this is source code.
2. Ingame, check your ‘Combat’ Channel and add in all combat related channels
    1. Right-Click to edit channel
    2. Move over all the combat fields if they’re not already there (Most likely, the pet combat fields won’t be included)
        1. If you don’t want to mess up or clutter that tab, you can make a new tab and put all the combat info in there. As long as all the combat data is being collected by at least one of your tabs, that data will be logged into the file.
    3. Save settings
3. Make sure you have **“Log Chat”** enabled in the Options
    1. This is found under **Options > Windows > Chat**
4. Run the .exe and browse for the log file
    1. Open up the directory where your game is installed to
    2. Then go to `/accounts/_YOUR_ACCOUNT_NAME_/logs/`
    3. Choose the log file you want to process or monitor (you’ll want the one dated to today if you’re running live)



### For Devs
Just in case you wanted to take a look around, the environment should be fairly straightforward to set up.

1. Make sure you have [Python](https://www.python.org/) (version 3.12) installed
2. Clone the repo and then create a _venv_ environemnt in the project directory and `pip install` the dependencies from requirements.txt
