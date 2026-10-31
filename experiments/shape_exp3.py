import math
import os

from locust import LoadTestShape

# Experiment 3: ramp up, hold, then drop to a low level so scale-out and scale-in both show.
# Set the peak from the Experiment 2 result (about 3x the knee): PEAK_USERS=24.
# Run with: PEAK_USERS=24 FILE_NAME=f1m.bin locust -f experiments/locustfile_files.py,experiments/shape_exp3.py
# One run takes ramp + hold + low = 5 + 10 + 18 = 33 minutes. The low phase is long because
# target tracking waits about 15 minutes of low metrics before it removes a task.
PEAK_USERS = int(os.environ.get("PEAK_USERS", "24"))


class FileRampShape(LoadTestShape):
    ramp_seconds = 5 * 60
    hold_seconds = 10 * 60
    low_seconds = 18 * 60
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
