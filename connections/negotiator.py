import sys

sys.path.append("..")

import socket
from schema import ConnectRequest, ConnectResponse, Machine, wire_decode
from connections.consts import NEGOTIATOR_IP, NEGOTIATOR_PORT
from utils import print_success


class Negotiator:
    """
    The negotiator is the driver for a program that exists just to help players
    connect to each other before the game begins. Once the game starts, the central
    negotiator is not needed since this is a peer-to-peer architecture
    """

    def __init__(self):
        self.machines: list[Machine] = []
        self.socket_map: dict[str, socket.socket] = {}
        self.port_num = 50000

    def negotiate(self):
        """
        Starts the negotiator server
        """
        # Listen for new player connections
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((NEGOTIATOR_IP, NEGOTIATOR_PORT))
        sock.listen()
        try:
            while len(self.machines) < 3:
                conn, addr = sock.accept()
                data = conn.recv(1024)
                if not data or len(data) <= 0:
                    continue
                req = wire_decode(data)
                if type(req) != ConnectRequest:
                    continue
                if req.name in self.socket_map:
                    conn.send(ConnectResponse(False).encode())
                    continue
                print_success(f"{req.name} accepted!")
                # First increment the number of listens of all existing machines
                for mach in self.machines:
                    mach.num_listens += 1
                # Now make the new machine and add it to the list
                new_mach = Machine(
                    name=req.name,
                    host_ip=addr[0],
                    input_port=self.port_num,
                    game_port=self.port_num + 1,
                    health_port=self.port_num + 2,
                    num_listens=0,
                    connections=[
                        [exist_mach.host_ip, exist_mach.input_port]
                        for exist_mach in self.machines
                    ],
                )
                self.port_num += 3
                self.machines.append(new_mach)
                self.socket_map[req.name] = conn
                # Let the machine know that it has been connected
                conn.send(ConnectResponse(True).encode())
        except Exception as e:
            sock.close()
        # All players have connected, tell them their identity
        for mach in self.machines:
            conn = self.socket_map[mach.name]
            conn.send(mach.encode())
            conn.close()


def create_negotiator():
    """
    Creates a negotiator and starts it
    """
    negotiator = Negotiator()
    negotiator.negotiate()
