from celery import Celery
app = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/0')
process_id = "d477174c-23e4-4702-9f8e-f71df3ce18c3"
app.send_task("tasks.task_b650_extract_section_a_information", args=[process_id])