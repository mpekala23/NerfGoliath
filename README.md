# NerfGoliath
A backend system for simple games that adaptively switches hosts to give losing players the lowest ping.

## Getting started

### Finding Your ip address
Windows: run `ipconfig /all`  and locate the IPv4 address for wireless LAN

Mac: run `ifconfig` and locate the IPv4 address and locate the `inet` address under `en0`

### Running the Game

To run the game locally simply update the ip addresses in `connections/consts.py` to your own machines ip address, ensure you have installed the correct requirements listed in `requirements.txt` then run the program `runner.py`. The will open a window for each player as well as a window that visualizes some of the communications happening between each process in the script.

To run the game across multiple computers update `connections/consts.py` with the ip of which ever computer is going to host the negotiator, run `connections/negotiator.py` and `connections/watcher.py` on the same computer. Then run:
```
python agent.py NAME
```
on the computer of each person playing the game, replacing `NAME` with a unique username for each player.

### Repository Structure