import sys

sys.path.append("..")

import time
import socket
import threading
from typing import Mapping
from queue import Queue
from threading import Thread
import connections.consts as consts
import errors
from connections.machine import Machine
from utils import print_error, print_info
from schema import Ping, Wireable, wire_decode


class ConnectionManager:
    """
    Handles the dirty work of opening sockets to the other machines.
    Abstracts to allow machines to operate at the level of sending
    messages based on machine name, ignoring underlying sockets.
    """

    def __init__(self, identity: Machine):
        self.identity = identity
        self.is_primary = False  # Is this the primary?
        self.living_siblings = consts.get_other_machines(identity.name)
        self.alive = True
        self.socket_map = {}
        self.wires_received: Queue[Wireable] = Queue()

    def initialize(self):
        """
        Does the work of initializing the connection manager
        @param progress: The progress of this machine (size of log)
        @param get_reqs_by_progress: A function that returns a list of requests
        that have been processed by this machine by progress count (can pass in lower and upper bound)
        """
        # First it should establish connections to all other internal machines
        listen_thread = Thread(target=self.listen_internally)
        connect_thread = Thread(target=self.handle_internal_connections)
        listen_thread.start()
        connect_thread.start()
        listen_thread.join()
        connect_thread.join()

        # At this point we assume that self.internal_sockets is populated
        # with sockets to all other internal machines
        for name, sock in self.socket_map.items():
            # Be sure to consume with the internal flag set to True
            consumer_thread = Thread(
                target=self.consume_internally,
                args=(
                    name,
                    sock,
                ),
            )
            consumer_thread.start()

        # Once all the servers are up we start doing health checks
        health_listen_thread = Thread(target=self.listen_health)
        health_listen_thread.start()
        health_probe_thread = Thread(target=self.probe_health)
        health_probe_thread.start()

    def listen_internally(self, sock=None):
        """
        Listens for incoming internal connections. Adds a connection to the socket
        map once connected, and repeats num_listens times.
        """
        # Setup the socket
        if not sock:
            # NOTE: The second parameter is only for unit testing purposes
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.identity.host_ip, self.identity.internal_port))
        sock.listen()
        # Listen the specified number of times
        listens_completed = 0
        try:
            while listens_completed < self.identity.num_listens:
                # Accept the connection
                conn, _ = sock.accept()
                # Get the name of the machine that connected
                name = conn.recv(2048).decode()
                # Add the connection to the map
                self.socket_map[name] = conn
                listens_completed += 1
            sock.close()
        except Exception as e:
            sock.close()

    def listen_health(self, sock=None):
        """
        Listens for incoming health checks, responds with PingResponse
        """
        if sock == None:
            self.health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.health_socket = sock
        self.health_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.health_socket.bind((self.identity.host_ip, self.identity.health_port))
        self.health_socket.listen()
        try:
            while self.alive:
                conn, _ = self.health_socket.accept()
                conn.recv(2048)
                conn.send(Ping().encode())
                conn.close()
        except:
            self.health_socket.close()

    def probe_health(self, sock_arg=None):
        """
        Sends a health check to every sibling regularly
        """
        FREQUENCY = 3  # seconds
        time.sleep(FREQUENCY)
        while self.alive:
            for sibling in self.living_siblings:
                sock = (
                    sock_arg
                    if sock_arg
                    else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                )
                sock.settimeout(FREQUENCY)
                try:
                    sock.connect((sibling.host_ip, sibling.health_port))
                    sock.send(Ping().encode())
                    sock.recv(2048)
                    sock.close()
                except:
                    print_error(f"Machine {sibling.name} is dead")
                    self.living_siblings.remove(sibling)
            if sock_arg:
                # For testing purposes
                break
            time.sleep(FREQUENCY)

    def connect_internally(self, name: str, progress: int, sock=None):
        """
        Connects to the machine with the given name
        NOTE: Can/is expected to sometimes throw errors
        """
        # Get the identity of the machine to connect to
        if name not in consts.MACHINE_MAP:
            print_error(f"Machine {name} is not in the identity map")
            print_error("Please recheck your configuration and try again")
            raise (errors.MachineNotFoundException("Invalid machine name"))
        identity = consts.MACHINE_MAP[name]
        # Setup the socket
        sock = sock if sock else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((identity.host_ip, identity.internal_port))
        # Send the name of this machine
        sock.send(self.identity.name.encode())
        # Add the connection to the map
        self.socket_map[name] = sock

    def consume_internally(self, name, conn):
        """
        Once a connection is established, open a thread that continuously
        listens for incoming requests
        """
        try:
            # NOTE: The use of timeout here is to ensure that we can
            # gracefully kill machines. Essentially the machine will check
            # in once a second to make sure it hasn't been killed, instead
            # of listening forever.
            while True:
                # Get the message
                msg = conn.recv(2048)
                if not msg or len(msg) <= 0:
                    raise Exception("Connection closed")
                self.wires_received.put(wire_decode(msg))
        except Exception:
            conn.close()

    def handle_internal_connections(self, progress: int):
        """
        Handles the connections to other machines
        """
        # Connect to the machines in the connection list
        for name in self.identity.connections:
            connected = False
            while not connected:
                try:
                    self.connect_internally(name, progress)
                    connected = True
                except Exception:
                    print_error(f"Failed to connect to {name}, retrying in 1 second")
                    time.sleep(1)

    def kill(self):
        """
        Kills the connection manager
        """
        self.alive = False
        for sock in list(self.socket_map.values()):
            # Helps prevent the weird "address is already in use" error
            try:
                sock.shutdown(1)
            except Exception:
                # Makes sure that we at least close every socket
                pass
            sock.close()
        if self.health_socket:
            self.health_socket.close()
