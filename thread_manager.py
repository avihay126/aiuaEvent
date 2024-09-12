
import concurrent.futures
import os
import threading
import queue
import time
import signal
import sys

import face_recognition
import logging
import logging_config

logger = logging.getLogger(__name__)




task_queue = queue.Queue()

executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

active_threads = 0
waiting_tasks = 0
active_threads_lock = threading.Lock()

face_lock = threading.Lock()
encoding_lock = threading.Lock()

shutdown_event = threading.Event()


def get_faces(image_path):
    with face_lock:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
    return image, face_locations


def get_encodings(image, face_locations):
    with encoding_lock:
        encodings = face_recognition.face_encodings(image, face_locations)
    return encodings


def submit_task(func, *args, **kwargs):
    global waiting_tasks

    task_queue.put((func, args, kwargs))
    with active_threads_lock:
        waiting_tasks += 1
        logger.info(f"Task added to queue. Waiting tasks: {waiting_tasks}")

    execute_from_queue()


def execute_from_queue():
    global active_threads, waiting_tasks

    with active_threads_lock:
        if active_threads < executor._max_workers and not shutdown_event.is_set():
            if not task_queue.empty():
                func, args, kwargs = task_queue.get()
                waiting_tasks -= 1
                active_threads += 1
                logger.info(f"Starting task. Active threads: {active_threads}, Waiting tasks: {waiting_tasks}")

                future = executor.submit(func, *args, **kwargs)
                future.add_done_callback(task_completed)


def task_completed(future):
    global active_threads

    with active_threads_lock:
        active_threads -= 1
        logger.info(f"Task completed. Active threads: {active_threads}")

    execute_from_queue()


def force_shutdown():
    if shutdown_event.is_set():
        logger.info("Task is stopping early due to shutdown.")
        return True
    return False



def remove_data():
    from core.models import ImageGroup, EventImage, SelfieImage, EventImageToImageGroup, Guest

    EventImageToImageGroup.objects.all().delete()
    ImageGroup.objects.all().delete()
    EventImage.objects.all().delete()
    SelfieImage.objects.all().delete()
    Guest.objects.all().delete()

    dirs = ["C:\\AiuaPhoto\\lavi_brit__18_08_2024", "C:\\AiuaPhoto\\hadar_avihay__21_03_2023", "C:\\AiuaPhoto\\yovel_uriel__23_05_2023"]

    for dir_path in dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # Iterate over all files in the directory
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)

                try:
                    # Check if it's a file and remove it
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing {file_path}: {e}")


def shutdown_gracefully(signal_num=None, frame=None):
    logger.info("Shutting down gracefully...")

    remove_data()

    with active_threads_lock:
        while not task_queue.empty():
            task_queue.get()

    shutdown_event.set()
    executor.shutdown(wait=False)

    logger.info("Server has shut down cleanly.")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_gracefully)
signal.signal(signal.SIGTERM, shutdown_gracefully)
