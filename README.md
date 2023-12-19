# coh-combat-parser
This program is a very basic (and very feature incomplete) combat log for City of Heroes. This is predominantly just a project that I could work on to get a some more coding experience but I’ve decided to make it available more widely to anyone who wants to use it, or expand on it a bit further. It is currently limited to just the data that can be pulled out from the log files, also this is **VERY ALPHA** code, expect things to break, expect results to maybe not be 100% accurate, but they should be close

This is also, by no means, intended to detract from the work Carnifax put into his online-based parser. In fact, he does have quite a bit more detail within his including handy charts and graphs that allow you to better see your damage peaks and troughs throughout a match

### What it can do

- Log outgoing damage from yourself and from your pets
    - Calculate overall DPS
    - Split DPS into individual passes / abilities and procs
    - Calculate the average damage per hit, per ability
- Log incoming damage to yourself
- Log Healing and Endurance recovery occurances
- Log hit accuracy
- Automatically start, pause and stop logs
    - A log will start when you take damage
    - Options to either pause the log or stop the log altogether if it has been several seconds since you last took or dealt damage

### What it can't do

- Make your coffee
- Parse data from other players (the combat logs don't provide visiblity to this data currently)
- factor in Regen
    - Again, this is a limitation on the information provided exclusively by chat logs