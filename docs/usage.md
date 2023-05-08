# Usage

This document outlines how you run this game over a network.

First, you must update `NEGOTIATOR_IP` and `NEGOTIATOR_PORT` in `connections/consts` to your IP and a reasonable port. Then do the same for `WATCHER_IP` and `WATCHER_PORT`.

Then, set `NUM_PLAYERS` to the desired value in `game/consts`.

Here is the order in which things should be booted up:

1. Run `python3 connections/negotiator.py`.
2. Run `python3 connections/watcher.py`.
3. Connect `NUM_PLAYERS` players by running `python3 agent.py <NAME_HERE>` with unique names for every player.
4. Enjoy! Once all the players connect, the game will automatically boot, with an additional watcher window to get a view of network traffic.

## An Easier Way

If you are running all the players on the same machine (for development purposes) it's simpler to just run `python3 runner.py`. This will automatically boot up `NUM_PLAYERS` players and give them AIs so they receive reasonable inputs.
