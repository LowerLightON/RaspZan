from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.classrooms import Room
from app.models.curriculum import Subject
from app.models.departments import Teacher
from app.models.groups import StudyGroup


@pytest.fixture()
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_group_lookup_returns_active_groups_sorted(
    client: TestClient,
    db: Session,
) -> None:
    inactive = StudyGroup(code="B-202", is_active=False)
    second = StudyGroup(code="C-303")
    first = StudyGroup(code="A-101")
    db.add_all([inactive, second, first])
    db.commit()

    response = client.get("/lookup/groups")

    assert response.status_code == 200
    assert response.json() == [
        {"id": first.id, "label": "A-101", "code": "A-101"},
        {"id": second.id, "label": "C-303", "code": "C-303"},
    ]


def test_teacher_lookup_returns_active_teachers_sorted(
    client: TestClient,
    db: Session,
) -> None:
    inactive = Teacher(
        last_name="Petrov",
        full_name="Petrov P.P.",
        is_active=False,
    )
    second = Teacher(last_name="Sidorov", full_name="Sidorov S.S.")
    first = Teacher(last_name="Ivanov", full_name="Ivanov I.I.")
    db.add_all([inactive, second, first])
    db.commit()

    response = client.get("/lookup/teachers")

    assert response.status_code == 200
    assert response.json() == [
        {"id": first.id, "label": "Ivanov I.I.", "full_name": "Ivanov I.I."},
        {"id": second.id, "label": "Sidorov S.S.", "full_name": "Sidorov S.S."},
    ]


def test_room_lookup_returns_active_rooms_sorted(
    client: TestClient,
    db: Session,
) -> None:
    inactive = Room(number="202", is_active=False)
    second = Room(number="303")
    first = Room(number="101")
    db.add_all([inactive, second, first])
    db.commit()

    response = client.get("/lookup/rooms")

    assert response.status_code == 200
    assert response.json() == [
        {"id": first.id, "label": "101", "number": "101"},
        {"id": second.id, "label": "303", "number": "303"},
    ]


def test_subject_lookup_returns_all_subjects_sorted(
    client: TestClient,
    db: Session,
) -> None:
    second = Subject(name="Physics")
    first = Subject(name="Math")
    db.add_all([second, first])
    db.commit()

    response = client.get("/lookup/subjects")

    assert response.status_code == 200
    assert response.json() == [
        {"id": first.id, "label": "Math", "name": "Math"},
        {"id": second.id, "label": "Physics", "name": "Physics"},
    ]
