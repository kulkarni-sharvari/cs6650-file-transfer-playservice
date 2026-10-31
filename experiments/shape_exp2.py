from locust import LoadTestShape


# Experiment 2: step load, to find where throughput stops growing for one file size. Kept in
# its own file because a LoadTestShape applies to every run and overrides -u/-r.
# Run with: FILE_NAME=f1m.bin locust -f experiments/locustfile_files.py,experiments/shape_exp2.py
# One run takes len(stages) * stage_seconds = 5 minutes.
class FileStepShape(LoadTestShape):
    stages = [2, 4, 8, 16, 32]  # users per stage; the gateway has 8 transfer slots
    stage_seconds = 60
    spawn_rate = 4  # users per second when moving to the next stage

    def tick(self):
        stage = int(self.get_run_time() // self.stage_seconds)
        if stage >= len(self.stages):
            return None  # ends the test
        return self.stages[stage], self.spawn_rate
