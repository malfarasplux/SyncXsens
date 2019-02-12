# SyncXsens
Synchrony exploration through a sensing lens (BITalino OpenSignals + python)

[1. Tools required](#prereq)  
[2. Extra resources](#resrc)  
[3. Configuration](#config)  


##  1. Tools required <a name="prereq"></a>
- Pyhton (v > 3.5)  
https://www.python.org/downloads/

- (Recommended) Anaconda + Python
 https://www.anaconda.com/download/

- (Recommended) BITalino revolution API  
https://pypi.org/project/bitalino/  
https://github.com/BITalinoWorld/revolution-python-api  

- PLUX BITalino OpenSignals (r)evolution Software  
https://bitalino.com/en/software

##  2. Other useful resources <a name="resrc"></a>  
- loopMIDI  
https://www.tobias-erichsen.de/software/loopmidi.html

- Dexed  
https://asb2m10.github.io/dexed/

##  3. Configuration <a name="config"></a>  
1. Ensure you count on a MIDI virtual port mapped to a MIDI software
2. Turn your device on and select the 2 channels used as RAW 100Hz  
![RAW](/img/RAW.jpg)

3. Set the TCP integreation checkbox ON and default port. 
4. When launched, make sure the websocket connects to your local TCP/IP. IP can be manually input in the code.
