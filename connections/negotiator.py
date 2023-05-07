import sys

sys.path.append("..")

import socket
from schema import ConnectRequest, ConnectResponse, Machine, wire_decode
from connections.consts import NEGOTIATOR_IP, NEGOTIATOR_PORT
from game.consts import NUM_PLAYERS
from utils import print_success
from tests.mocks.mock_socket import socket as mock_socket
from typing import Union


class Negotiator:
    """
    The negotiator is the driver for a program that exists just to help players
    connect to each other before the game begins. Once the game starts, the central
    negotiator is not needed since this is a peer-to-peer architecture
    """

    def __init__(self):
        self.machines: list[Machine] = []
        self.socket_map: dict[str, Union[socket.socket, mock_socket]] = {}
        self.port_num = 50000

    def negotiate(self, test_sock: Union[mock_socket, None] = None):
        """
        Starts the negotiator server
        """
        # Listen for new player connections
        sock = (
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if test_sock == None
            else test_sock
        )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((NEGOTIATOR_IP, NEGOTIATOR_PORT))
        sock.listen()
        try:
            while len(self.machines) < NUM_PLAYERS:
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
                new_mach = Machine(
                    name=req.name,
                    host_ip=addr[0],
                    port=self.port_num,
                    connections=[
                        [exist_mach.host_ip, exist_mach.port]
                        for exist_mach in self.machines
                    ],
                )
                self.port_num += 1
                self.machines.append(new_mach)
                self.socket_map[req.name] = conn
                # Let the machine know that it has been connected
                conn.send(
                    ConnectResponse(True, is_leader=len(self.machines) == 1).encode()
                )
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


if __name__ == "__main__":
    create_negotiator()
