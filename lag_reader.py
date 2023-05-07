# read in the lag files and plot the lag vs. time

import matplotlib.pyplot as plt
import numpy as np



def lag_reader(input_times_f, rec_times_f):
    input_times = []
    rec_time = []

    # read in the lag files
    with open(input_times_f, "r") as f:
        up_input_times = f.readlines()
        input_times = [float(x) for x in up_input_times]

    with open(rec_times_f, "r") as f:
        rec_time = f.readlines()
        rec_time = [float(x) for x in rec_time]

    # Find the difference between the input time and the next highest rec time
    diff = []
    for i in range(len(input_times)):
        for i in range(len(rec_time)):
            if input_times[i] < rec_time[i]:
                diff.append(rec_time[i] - input_times[i])
                break
    return diff


leader_lag = lag_reader("up_input_times_leader.txt", "rec_time_leader.txt")
follower_lag = lag_reader("up_input_times_follower.txt", "rec_time_follower.txt")

# plot bar graphof the lag of the leader and follower with error bars
plt.bar(
    ["Leader", "Follower"],
    [np.mean(leader_lag), np.mean(follower_lag)],
)
plt.title("Lag of Leader vs. Follower")
plt.xlabel("Leader vs. Follower")
plt.ylabel("Lag (s)")
plt.show()

