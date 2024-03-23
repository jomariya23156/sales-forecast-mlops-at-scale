import os
import time
from ray.job_submission import JobSubmissionClient, JobStatus

RAY_DASHBOARD_PORT = os.getenv("RAY_DASHBOARD_PORT", "8265")

client = JobSubmissionClient(f"http://ray:{RAY_DASHBOARD_PORT}")
job_id = client.submit_job(
    entrypoint="python ray_test_job.py", runtime_env={"working_dir": "./"}
)
print("job_id:", job_id)


def wait_until_status(job_id, status_to_wait_for, timeout_seconds=30):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        status = client.get_job_status(job_id)
        print(f"status: {status} | type {type(status)}")
        # if status in status_to_wait_for:
        #     break
        if str(status) in status_to_wait_for:
            break
        time.sleep(1)


start = time.time()
# wait_until_status(job_id, {JobStatus.SUCCEEDED, JobStatus.STOPPED, JobStatus.FAILED})
wait_until_status(job_id, {"SUCCEEDED", "STOPPED", "FAILED"})
logs = client.get_job_logs(job_id)
print(logs)
print(f"Total time spent: {time.time() - start:.4f} s")
