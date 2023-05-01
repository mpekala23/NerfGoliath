from connections import consts
from multiprocessing import Process
from agent import create_agent
from connections.negotiator import create_negotiator


"""
def old_run_local_game():
    pA = Process(target=create_agent, args=((consts.MACHINE_A,)))
    pB = Process(target=create_agent, args=((consts.MACHINE_B,)))

    pA.start()
    pB.start()

    pA.join()
    pB.join()
"""


def run_local_game():
    pNeg = Process(target=create_negotiator)
    pA = Process(target=create_agent, args=(("A",)))
    pB = Process(target=create_agent, args=(("B",)))
    pC = Process(target=create_agent, args=(("C",)))
    pD = Process(target=create_agent, args=(("D",)))

    pNeg.start()
    pA.start()
    pB.start()
    pC.start()
    pD.start()

    pNeg.join()
    pA.join()
    pB.join()
    pC.join()
    pD.join()


if __name__ == "__main__":
    run_local_game()
