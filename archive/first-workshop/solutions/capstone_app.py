"""Completed task-board reference: copy into capstone/app.py to run."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, StringConstraints


class NewTask(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class Task(NewTask):
    id: str
    completed: bool = False


class TaskUpdate(BaseModel):
    completed: bool


def create_app() -> FastAPI:
    app = FastAPI(title="Workshop task board")
    tasks: dict[str, Task] = {}

    def find_task(task_id: str) -> Task:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        return tasks[task_id]

    @app.get("/", response_class=FileResponse)
    def homepage() -> FileResponse:
        return FileResponse(Path(__file__).with_name("index.html"))

    @app.get("/tasks")
    def list_tasks() -> list[Task]:
        return list(tasks.values())

    @app.post("/tasks", status_code=201)
    def add_task(new: NewTask) -> Task:
        task = Task(id=str(uuid4()), title=new.title)
        tasks[task.id] = task
        return task

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str) -> Task:
        return find_task(task_id)

    @app.patch("/tasks/{task_id}")
    def update_task(task_id: str, update: TaskUpdate) -> Task:
        task = find_task(task_id)
        updated = task.model_copy(update={"completed": update.completed})
        tasks[task_id] = updated
        return updated

    @app.delete("/tasks/{task_id}", status_code=204)
    def delete_task(task_id: str) -> Response:
        find_task(task_id)
        del tasks[task_id]
        return Response(status_code=204)

    return app


app = create_app()
