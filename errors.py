# An exception type for non-existent machines
class MachineNotFoundException(Exception):
    def __init__(self, name: str):
        self.name = name
        self.message = f"Machine {name} is not in the identity map"
        super().__init__(self.message)


# An exception for when an invalid message tries to be decoded
class InvalidMessage(Exception):
    def __init__(self, s: str):
        self.s = s
        self.message = f"Invalid wired message: {s}"
        super().__init__(self.message)


# An exception for an unknown communication request
class UnknownComms(Exception):
    def __init__(self, s: str):
        self.s = s
        self.message = f"Unknown comms request: {s}"
        super().__init__(self.message)


# An exception for when comms go down randomly
class CommsDied(Exception):
    def __init__(self, s: str):
        self.s = s
        self.message = f"Comms died, {s}"
        super().__init__(self.message)
