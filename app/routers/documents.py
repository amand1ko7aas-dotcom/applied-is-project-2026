from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlmodel import Session, select
from app.database.db import get_session
from app.database.models import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    Employee,
    Kafedra,
    LoginRequest,
    Task,
    TaskCreate,
    TaskUpdate,
    UserAccount,
)

router = APIRouter(tags=["АРМ Хатшы — Құжат айналымы"])


@router.post("/auth/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(
        select(UserAccount).where(
            UserAccount.username == payload.username,
            UserAccount.password == payload.password,
        )
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Логин немесе құпиясөз қате")
    return {
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "token": f"role:{user.role}",
    }


@router.get("/admin/users", response_model=List[UserAccount])
def list_users(
    x_user_role: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    if not x_user_role:
        raise HTTPException(status_code=401, detail="Авторизация қажет (X-User-Role)")
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Тек сайт басқарушысына (admin) рұқсат етілген")
    return session.exec(select(UserAccount)).all()


@router.get("/documents", response_model=List[Document])
def list_documents(
    search: Optional[str] = Query(default=None, description="Құжат нөмірі немесе тақырыбы бойынша іздеу"),
    doc_type: Optional[str] = Query(default=None, description="Құжат түрі (Бұйрық, Өкім, Хат...)"),
    doc_status: Optional[str] = Query(default=None, description="Мәртебесі (Орындалуда, Бекітілді, Мұрағатталған)"),
    session: Session = Depends(get_session),
):
    stmt = select(Document)
    if search:
        stmt = stmt.where(Document.topic.contains(search) | Document.doc_number.contains(search))
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)
    if doc_status:
        stmt = stmt.where(Document.status == doc_status)
    return session.exec(stmt.order_by(Document.id.desc())).all()


@router.get("/documents/{doc_id}", response_model=Document)
def get_document(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Құжат табылмады")
    return doc


@router.post("/documents", response_model=Document, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate, session: Session = Depends(get_session)):
    db_doc = Document.model_validate(payload)
    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)
    return db_doc


@router.patch("/documents/{doc_id}", response_model=Document)
def update_document(
    doc_id: int,
    payload: DocumentUpdate,
    session: Session = Depends(get_session),
):
    db_doc = session.get(Document, doc_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Құжат табылмады")

    update_data = payload.model_dump(exclude_unset=True)
    db_doc.sqlmodel_update(update_data)
    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)
    return db_doc


@router.delete("/documents/{doc_id}", status_code=status.HTTP_200_OK)
def delete_document(doc_id: int, session: Session = Depends(get_session)):
    db_doc = session.get(Document, doc_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Құжат табылмады")

    session.delete(db_doc)
    session.commit()
    return {"message": f"Құжат ID={doc_id} сәтті жойылды"}


@router.get("/tasks", response_model=List[Task])
def list_tasks(
    task_status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Task)
    if task_status:
        stmt = stmt.where(Task.status == task_status)
    return session.exec(stmt.order_by(Task.id.desc())).all()


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)):
    doc = session.get(Document, payload.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Байланысты құжат табылмады")
    emp = session.get(Employee, payload.executor_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Орындаушы қызметкер табылмады")

    task = Task.model_validate(payload)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Тапсырма табылмады")
    task.sqlmodel_update(payload.model_dump(exclude_unset=True))
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.get("/kafedra", response_model=List[Kafedra])
def list_kafedra(session: Session = Depends(get_session)):
    return session.exec(select(Kafedra)).all()


@router.get("/employees", response_model=List[Employee])
def list_employees(session: Session = Depends(get_session)):
    return session.exec(select(Employee)).all()
