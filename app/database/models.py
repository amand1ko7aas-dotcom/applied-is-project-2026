from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class Kafedra(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=1)
    head_name: str = Field(min_length=1)
    office: str = Field(min_length=1)

    employees: List["Employee"] = Relationship(back_populates="kafedra")


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(index=True, min_length=1)
    position: str = Field(min_length=1)
    phone: Optional[str] = None
    email: Optional[str] = None
    kafedra_id: Optional[int] = Field(default=None, foreign_key="kafedra.id")

    kafedra: Optional[Kafedra] = Relationship(back_populates="employees")
    tasks: List["Task"] = Relationship(back_populates="executor")


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doc_number: str = Field(index=True, min_length=1)
    doc_type: str = Field(default="Бұйрық")
    reg_date: str = Field(default="2026-02-15")
    topic: str = Field(index=True, min_length=1)
    status: str = Field(default="Орындалуда")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tasks: List["Task"] = Relationship(back_populates="document")


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    executor_id: int = Field(foreign_key="employee.id")
    task_text: str = Field(min_length=1)
    deadline: str = Field(default="2026-03-05")
    status: str = Field(default="Орындалуда")

    document: Optional[Document] = Relationship(back_populates="tasks")
    executor: Optional[Employee] = Relationship(back_populates="tasks")


class UserAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=1)
    password: str = Field(min_length=4)
    full_name: str = Field(min_length=1)
    role: str = Field(default="secretary")


class DocumentCreate(SQLModel):
    doc_number: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)
    reg_date: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    status: str = Field(default="Орындалуда")


class DocumentUpdate(SQLModel):
    doc_number: Optional[str] = Field(default=None, min_length=1)
    doc_type: Optional[str] = Field(default=None, min_length=1)
    reg_date: Optional[str] = Field(default=None, min_length=1)
    topic: Optional[str] = Field(default=None, min_length=1)
    status: Optional[str] = Field(default=None, min_length=1)


class TaskCreate(SQLModel):
    document_id: int
    executor_id: int
    task_text: str = Field(min_length=1)
    deadline: str = Field(min_length=1)
    status: str = Field(default="Орындалуда")


class TaskUpdate(SQLModel):
    task_text: Optional[str] = Field(default=None, min_length=1)
    deadline: Optional[str] = Field(default=None, min_length=1)
    status: Optional[str] = Field(default=None, min_length=1)


class LoginRequest(SQLModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
