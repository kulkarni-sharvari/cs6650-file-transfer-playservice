import os

from locust import FastHttpUser, task

# The file every request fetches, set per run: FILE_NAME=f64k.bin locust -f ...
# Files live under tmp/ in the S3 bucket (f4k.bin, f64k.bin, f1m.bin, f4m.bin).
FILE_NAME = os.environ.get("FILE_NAME", "f64k.bin")


# FastHttpUser with no wait_time, so each user sends its next request as soon as the
# previous one returns. The timeout is above the client's worst case of about 20s (5 OPEN
# attempts plus 5 RETY rounds at 2s each) and the ALB's 60s idle timeout, so a slow request
# fails on the gateway's answer, not on Locust giving up first.
#
# Run Experiment 1 with -u/-r (fixed users):
#   FILE_NAME=f64k.bin locust -f experiments/locustfile_files.py --host http://<alb> \
#       --headless -u 4 -r 4 -t 5m --csv shots/exp1/10_0
# Run Experiments 2 and 3 with a shape file, which sets the users instead of -u/-r:
#   FILE_NAME=f1m.bin locust -f experiments/locustfile_files.py,experiments/shape_exp2.py ...
class FileUser(FastHttpUser):
    network_timeout = 60.0
    connection_timeout = 60.0

    @task
    def get_file(self):
        # catch_response lets us label each failure with its status code, so the Failures
        # tab separates 503 (gateway queue full) from 504 (file server did not respond).
        with self.client.get(f"/files?name={FILE_NAME}", name="GET /files",
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"{response.status_code}")
