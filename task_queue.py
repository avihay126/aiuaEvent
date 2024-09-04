# task_queue.py
import threading
from queue import Queue

# יצירת תור משימות
task_queue = Queue(maxsize=3)

def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        try:
            task()
        finally:
            task_queue.task_done()

# הרצת ה-worker
for i in range(3):
    threading.Thread(target=worker, daemon=True).start()

def add_task(task):
    task_queue.put(task)
