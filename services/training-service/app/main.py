import os
import ray
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray.job_submission import JobSubmissionClient, JobStatus

RAY_DASHBOARD_HOST = os.getenv("RAY_DASHBOARD_HOST", "ray")
RAY_DASHBOARD_PORT = os.getenv("RAY_DASHBOARD_PORT", "8265")

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

ray_job_client = JobSubmissionClient(
    f"http://{RAY_DASHBOARD_HOST}:{RAY_DASHBOARD_PORT}"
)

app = FastAPI()


@app.post("/train", status_code=200)
async def train(request: Request):

    train_job_id = ray_job_client.submit_job(
        entrypoint="python ray_train_all_job.py", runtime_env={"working_dir": "./"}
    )
    logging.info("Submitted a training job for ALL models to Ray")
    logging.info(f"Training job id: {train_job_id}")

    return {
        "train_job_id": train_job_id,
        "status": "SUBMITTED",
    }


@app.post("/{store_id}/{product_name}/train", status_code=200)
async def train_one(store_id: int, product_name: str):

    train_job_id = ray_job_client.submit_job(
        entrypoint=f"python ray_train_one_job.py --store_id={store_id} --product_name={product_name}",
        runtime_env={"working_dir": "./"},
    )
    logging.info(
        f"Submitted a training job for store {store_id} product {product_name} to Ray"
    )
    logging.info(f"Training job id: {train_job_id}")

    return {
        "train_job_id": train_job_id,
        "status": "SUBMITTED",
    }


@app.get("/training_job_status/{train_job_id}")
async def training_job_status(train_job_id: str):
    try:
        status = ray_job_client.get_job_status(train_job_id)
    except Exception as e:
        logging.exception(e)
        return JSONResponse(
            status_code=400,
            content={
                "train_job_id": train_job_id,
                "status": "ERROR",
                "error": "Task not found",
            },
        )
    return {"train_job_id": train_job_id, "status": str(status)}
