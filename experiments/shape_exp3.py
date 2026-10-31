import math
import os

from locust import LoadTestShape

# Experiment 3: ramp up, hold, then drop to a low level so scale-out and scale-in both show.
# Set the peak from the Experiment 2 result (about 3x the knee): PEAK_USERS=24.
# Set the length of the hold and low phases in minutes with HOLD_MIN (default 5) and LOW_MIN
# (default 18).
# Run with: PEAK_USERS=24 FILE_NAME=f64k.bin locust -f experiments/locustfile_files.py,experiments/shape_exp3.py
# The control run (scaling off) never scales in, so use LOW_MIN=5 for it: 5 + 5 + 5 = 15 minutes.
# The autoscaled run keeps the default 5 + 5 + 18 = 28 minutes. The low phase is long because
# target tracking waits about 15 minutes of low metrics before it removes a task.
PEAK_USERS = int(os.environ.get("PEAK_USERS", "24"))
HOLD_MIN = float(os.environ.get("HOLD_MIN", "5"))
LOW_MIN = float(os.environ.get("LOW_MIN", "18"))


class FileRampShape(LoadTestShape):
    ramp_seconds = 5 * 60
    hold_seconds = HOLD_MIN * 60
    low_seconds = LOW_MIN * 60
    low_fraction = 0.1  # users during the low phase, as a share of the peak

    def tick(self):
        t = self.get_run_time()
        low_users = max(1, round(PEAK_USERS * self.low_fraction))
        if t < self.ramp_seconds:
            # Climb in a straight line; a spawn rate of 1 is faster than the climb needs.
            return max(1, math.ceil(PEAK_USERS * t / self.ramp_seconds)), 1
        if t < self.ramp_seconds + self.hold_seconds:
            return PEAK_USERS, 1
        if t < self.ramp_seconds + self.hold_seconds + self.low_seconds:
            return low_users, PEAK_USERS  # drop at once
        return None  # ends the test
