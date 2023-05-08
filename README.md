# NerfGoliath

A backend system for simple games that adaptively switches hosts to give losing players the lowest ping.

## Getting started

### Finding Your ip address

Windows: run `ipconfig /all` and locate the IPv4 address for wireless LAN

Mac: run `ifconfig` and locate the IPv4 address and locate the `inet` address under `en0`

### Running the Game

To run the game locally simply update the ip addresses in `connections/consts.py` to your own machines ip address (or simply `127.0.0.1`), ensure you have installed the correct requirements listed in `requirements.txt` then run the program `runner.py`. The will open a window for each player as well as a window that visualizes some of the communications happening between each process in the script.

To run the game across multiple computers update `connections/consts.py` with the ip of which ever computer is going to host the negotiator, run `connections/negotiator.py` and `connections/watcher.py` on the same computer. Then run:

```
python agent.py NAME
```

on the computer of each person playing the game, replacing `NAME` with a unique username for each player.

## Files

This document serves a directory for the entire project. Please consult the `docs` folder and the final report for more technical details.

### `docs`

- `architecture.md` - Explains the system design at a high level.
- `installation.md` - How to install the dependencies
- `usage.md` - How to run the game

### `connections`

- `consts.py` - Useful global constants to have to help configure communication in the system
- `machine.py` - Represents the identity of a player, and information needed to identify them for communication
- `manager.py` - The class responsible for sending things over the wire. Very nice to have abstracted as it's own class so that the logic in the player code can be as simple as possible
- `negotiator.py` - The service responsible for introducing players to each other at the beginning of the game to establish peer-to-peer communications
- `watcher.py` - A helpful tool to visualize all communications in the network

### `game`

- `assets` - Sprites
- `shaders` - Unused
- `standalone` - A standalone version of the game that does not support multiple players
- `ai.py` - Logic for very simple ai controllers useful to have around while testing
- `consts.py` - Useful global variables for defining the game
- `game.py` - The logic of the game itself, including abstractions for input, drawing, frame updates, etc.
- `player_sprite.py` - The logic for drawing and receiving updates specifically on the player models
- `spell_sprite.py` - Same as above but for spells

### `output`

Output from the logs during experiments

### `results`

Results from our experiments

### `tests`

Unit tests for the important parts of our system

### `agent.py`

The code that is run by a single player to play the game. Is really more of a "client" than an agent

### `errors.py`

Common errors used across the project.

### `runner.py`

Runs a suite of AI locally to test the game.

### `schema.py`

ALl useful classes and data structures used in the project. Also contains our wire protocol.

### `utils.py`

Useful printing functions.
