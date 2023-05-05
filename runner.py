from connections import consts
from multiprocessing import Process
from agent import create_agent
from connections.negotiator import create_negotiator
from connections.watcher import create_watcher
from game.consts import NUM_PLAYERS

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
    pWat = Process(target=create_watcher)
    names = "ABCDEFG"
    player_procs = []
    for name in names[:NUM_PLAYERS]:
        proc = Process(target=create_agent, args=((name,)))
        player_procs.append(proc)

    pNeg.start()
    pWat.start()
    for proc in player_procs:
        proc.start()

    pNeg.join()
    pWat.join()
    for proc in player_procs:
        proc.join()


if __name__ == "__main__":
    run_local_game()
