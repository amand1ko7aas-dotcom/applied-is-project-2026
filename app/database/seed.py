from sqlmodel import Session, select
from app.database.db import engine, init_db
from app.database.models import Document, Employee, Kafedra, Task, UserAccount


def run_seed() -> None:
    init_db()
    with Session(engine) as session:
        if session.exec(select(Kafedra)).first():
            print("Деректер қоры (АРМ Хатшы) бұрын толтырылған.")
            return

        u1 = UserAccount(
            username="hatshy",
            password="1234",
            full_name="Айтбаева Г.А.",
            role="secretary",
        )
        u2 = UserAccount(
            username="admin",
            password="admin",
            full_name="Амандық Сабина",
            role="admin",
        )
        session.add_all([u1, u2])
        session.commit()

        kaf = Kafedra(
            name="Ақпараттық жүйелер және ИТ кафедрасы",
            head_name="Нұрланұлы Қ.Т.",
            office="305-каб",
        )
        session.add(kaf)
        session.commit()

        emp1 = Employee(
            full_name="Оспанов Е.Б.",
            position="Қауымдастырылған профессор",
            phone="+7 701 111 22 33",
            email="ospanov@edu.kz",
            kafedra_id=kaf.id,
        )
        emp2 = Employee(
            full_name="Серікова Ә.М.",
            position="Аға оқытушы",
            phone="+7 702 222 33 44",
            email="serikova@edu.kz",
            kafedra_id=kaf.id,
        )
        emp3 = Employee(
            full_name="Айтбаева Г.А.",
            position="Кафедра хатшысы",
            phone="+7 705 333 44 55",
            email="aitbaeva@edu.kz",
            kafedra_id=kaf.id,
        )
        session.add_all([emp1, emp2, emp3])
        session.commit()

        doc1 = Document(
            doc_number="№ 14-08/112",
            doc_type="Бұйрық",
            reg_date="2026-02-15",
            topic="2026-2027 оқу жылына арналған оқу жүктемесі",
            status="Бекітілді",
        )
        doc2 = Document(
            doc_number="№ 14-08/119",
            doc_type="Өкім",
            reg_date="2026-02-22",
            topic="Өндірістік тәжірибеден өту туралы",
            status="Орындалуда",
        )
        doc3 = Document(
            doc_number="№ 14-08/125",
            doc_type="Қызметтік жазба",
            reg_date="2026-03-01",
            topic="ИС-24-А1 тобының курстық жобаларын қорғау кестесі",
            status="Орындалуда",
        )
        session.add_all([doc1, doc2, doc3])
        session.commit()

        t1 = Task(
            document_id=doc1.id,
            executor_id=emp1.id,
            task_text="Оқудан шығарылатын студенттер тізімін дайындау",
            deadline="2026-02-28",
            status="Орындалуда",
        )
        t2 = Task(
            document_id=doc2.id,
            executor_id=emp2.id,
            task_text="Жұмыс оқу бағдарламаларын (Силлабустарды) жаңарту",
            deadline="2026-03-05",
            status="Аяқталды",
        )
        t3 = Task(
            document_id=doc1.id,
            executor_id=emp3.id,
            task_text="Дипломдық жұмыс жетекшілерін бекіту хаттамасын тексеру",
            deadline="2026-02-20",
            status="Мерзімі өткен",
        )
        session.add_all([t1, t2, t3])
        session.commit()
        print("АРМ Хатшы деректер қоры сәтті толтырылды!")


if __name__ == "__main__":
    run_seed()
