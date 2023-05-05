from queue import Queue


class socket:
    """
    A class that simulates all the important aspects of a socket
    for testing purposes
    """

    def __init__(self, _, __):
        self.has_closed = False
        self.fake_sends = Queue()
        self.binded_to = None
        self.connected_to = None
        self.has_listened = False
        self.fake_connects = []
        self.sent: list[bytes] = []

    # HELPER FUNCTIONS

    def add_fake_send(self, data: bytes):
        """
        Makes it so the next call to recv will return the given message
        encoded as a bytestring
        """
        self.fake_sends.put(data)

    # MOCKED FUNCTIONS

    def close(self):
        self.has_closed = True

    def recv(self, _) -> bytes:
        if self.has_closed:
            raise Exception("Socket has been closed")
        if self.fake_sends.empty():
            raise Exception("No more messages to send")
        return self.fake_sends.get()

    def settimeout(self, _):
        pass

    def setsockopt(self, _, __, ___):
        pass

    def getpeername(self):
        return (1, "peer")

    def bind(self, tup):
        self.binded_to = tup

    def listen(self):
        self.has_listened = True

    def accept(self):
        return self, ""

    def connect(self, tup):
        self.connected_to = tup

    def send(self, bs: bytes):
        self.sent.append(bs)
