# Architecture

This document outlines the high level structure of our system.

## Table of Contents

1. [Coordinating the Game](#coordinating-the-game)
2. [Leader Switches](#leader-switches)

## Coordinating the Game

We wanted to make our game be able to support a dynamic number of players. To do this we implemented a negotiator service in `negotiator.py`. Essentially, it will have a known IP/port combination and exist solely to listen for new players.

When a new player wishes to join the game, they reach out to the `negotiator` and receive a response. If they provided a unique name and there is still space in the game, the response is `True`. Otherwise it is `False` and the player must try again.

### Setting Up Connections

A big benefit of having a central `negotiator` is that we can determine an efficient way to have the players establish communication. When the `negotiator` decides to start the game (all players have connected) it will reach out to each player with a list of other players they are responsible for `connect`ing to. (NOTE: All players are always listening for incoming connections on a port prescribed by the `negotiator`.)
