import pdb
import schema as data_schema
from typing import List
import sys

sys.path.append("..")


class Machine:
    """
    A class that represents the identity of a machine. Most crucially
    this stores information about which ip/port the machine is listening
    on, as well as which other machines it is responsible for connecting
    to.
    """

    def __init__(
        self,
        name: str,
        host_ip: str,
        internal_port: int,
        client_port: int,
        health_port: int,
        notif_port: int,
        num_listens: int,
        connections: List[str],
    ) -> None:
        # The name of the machine (in our experiments "A" | "B" | "C")
        self.name = name
        # The ip address the machine should listen on for new connections
        self.host_ip = host_ip
        # The port the machine should listen on for connections from other machines
        self.internal_port = internal_port
        # The port the machine should listen on for connections to clients
        self.client_port = client_port
        # The port the machine should listen on for health checks
        self.health_port = health_port
        # The port the machine should listen on for notification sub requests
        self.notif_port = notif_port
        # The number of connections the machine should listen for
        self.num_listens = num_listens
        # The names of the machines that this machine should connect to
        self.connections = connections
