import logging
import multiprocessing
import socket

from redis import Redis
from rq import Queue, Worker

from ..core.config import settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def run_worker(index: int, *, with_scheduler: bool = False) -> None:
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue(settings.INGESTION_QUEUE_NAME, connection=redis_conn)
    worker_name = f"ingestion-{socket.gethostname()}-{index}"
    logger.info("Starting ingestion worker %s for queue %s", worker_name, settings.INGESTION_QUEUE_NAME)
    worker = Worker([queue], connection=redis_conn, name=worker_name)
    worker.work(with_scheduler=with_scheduler)


def main() -> None:
    concurrency = max(1, settings.INGESTION_WORKER_CONCURRENCY)
    if concurrency == 1:
        run_worker(1, with_scheduler=True)
        return

    processes: list[multiprocessing.Process] = []
    for index in range(1, concurrency + 1):
        process = multiprocessing.Process(
            target=run_worker,
            kwargs={"index": index, "with_scheduler": index == 1},
            daemon=False,
        )
        process.start()
        processes.append(process)

    for process in processes:
        process.join()


if __name__ == "__main__":
    main()
