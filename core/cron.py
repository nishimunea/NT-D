import concurrent.futures
import time

import requests

REM_SERVER_HOST = "http://127.0.0.1:5000/"

PENDING_TASK_ENDPOINT = "task/pending/"
RUNNING_TASK_ENDPOINT = "task/running/"
STOPPED_TASK_ENDPOINT = "task/stopped/"
TASK_SCHEDULE_ENDPOINT = "task/schedule/"

PENDING_TASK_INTERVAL = 10
RUNNING_TASK_INTERVAL = 10
STOPPED_TASK_INTERVAL = 10
TASK_SCHEDULE_INTERVAL = 10


def handlePendingTask():
    while True:
        invoke(PENDING_TASK_ENDPOINT)
        time.sleep(PENDING_TASK_INTERVAL)


def handleRunningTask():
    while True:
        invoke(RUNNING_TASK_ENDPOINT)
        time.sleep(RUNNING_TASK_INTERVAL)


def handleStoppedTask():
    while True:
        invoke(STOPPED_TASK_ENDPOINT)
        time.sleep(STOPPED_TASK_INTERVAL)


def handleTaskSchedule():
    while True:
        invoke(TASK_SCHEDULE_ENDPOINT)
        time.sleep(TASK_SCHEDULE_INTERVAL)


def invoke(endpoint):
    headers = {"X-AppEngine-Cron": "true"}
    url = REM_SERVER_HOST + endpoint
    return requests.get(url, headers=headers)


def main():
    executor = concurrent.futures.ThreadPoolExecutor()
    executor.submit(handlePendingTask)
    executor.submit(handleRunningTask)
    executor.submit(handleStoppedTask)
    executor.submit(handleTaskSchedule)


print(' * Serving local task scheduler "cron.py"')


if __name__ == "__main__":
    main()
