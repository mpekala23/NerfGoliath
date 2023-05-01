from connections import consts
from multiprocessing import Process
from agent import create_agent


def run_local_game():
    pA = Process(target=create_agent, args=((consts.MACHINE_A,)))
    pB = Process(target=create_agent, args=((consts.MACHINE_B,)))

    pA.start()
    pB.start()

    pA.join()
    pB.join()


if __name__ == "__main__":
    run_local_game()
