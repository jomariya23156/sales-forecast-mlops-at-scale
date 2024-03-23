import os
import time
import ray
from ray.util.state import summarize_actors, summarize_tasks, list_actors, list_jobs

ray.init()

# @ray.remote
# def wait_til_task_done(obj_ref):
#     obj = ray.get(obj_ref)
#     print("ALL tasks are now done! yoohoo")


@ray.remote
def wanna_sleep(person, msg):
    print(f"person: {person} | msg: {msg}")
    time.sleep(10)
    return person + " " + msg


persons = ["Jom", "Earth"]
msgs = ["sleep", "eat"]

obj_refs = list([wanna_sleep.remote(person, msg) for person in persons for msg in msgs])
# wait_til_task_done.remote(obj_refs)
obj = ray.get(obj_refs)
print("ALL tasks are now done! yoohoo")
