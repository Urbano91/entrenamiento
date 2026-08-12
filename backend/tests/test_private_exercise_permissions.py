from __future__ import annotations

import asyncio
from datetime import date, time, timedelta
from io import BytesIO
from http.cookies import SimpleCookie

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.auth import (
    change_provisional_password,
    complete_onboarding,
    get_current_user,
    login as auth_login,
    router as auth_router,
    user_payload,
    verify_password,
)
from app.api.admin import (
    AdminClubCreate, AdminTrainerCreate, create_club as admin_create_club,
    create_trainer as admin_create_trainer, delete_club as admin_delete_club,
    delete_user as admin_delete_user,
)
from app.api.club import (
    ClubTrainerCreate, ClubTrainerVisibilityIn, _coordination_workbook,
    coordination, create_club_trainer, list_trainers, router as club_router,
    set_trainer_visibility,
)
from app.api.calendario import get_calendario
from app.api import ejercicios as ejercicios_api
from app.api.ejercicios import (
    create_ejercicio,
    delete_ejercicio,
    get_ejercicio,
    similares_ejercicios,
    update_ejercicio,
    upload_ejercicio_image,
    delete_ejercicio_image,
)
from app.api.entrenamientos import (
    EntrenamientoCreate, EntrenamientoUpdate, ReutilizarIn,
    create_entrenamiento, delete_entrenamiento, reutilizar_entrenamiento,
    update_entrenamiento,
)
from app.api.temporadas import TemporadaCreate, create_temporada
from app.api.planificaciones import NotaIn, save_note
from app.db.database import Base
from app.models.models import (
    CategoriaObjetivo,
    Club,
    CoachAssignment,
    Ejercicio,
    EjercicioObjetivoV2,
    Entrenamiento,
    Espacio,
    ExerciseOwnership,
    ObjetivoNormalizadoV2,
    PerfilEntrenador,
    Partido,
    PlanificacionDiaria,
    SportsCategory,
    TaxonomiaObjetivoVersion,
    Temporada,
    Tiempo,
    TipoTarea,
    UserAccount,
    Usuario,
)
from app.schemas.schemas import (
    EjercicioCreate, EjercicioUpdate, OnboardingComplete,
    ProvisionalPasswordChange, UsuarioLogin,
)
from app.scripts.create_user import get_password_hash
from app.services.permissions import (
    can_view_exercise, require_admin,
    visible_exercise_filter,
)
from app.services.storage import LocalStorageService
from app.services.trainer_colors import trainer_color
from app.services.taxonomy import exercise_taxonomy_filter


@pytest.fixture()
def security_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'security.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)
    db = Session()
    users = [
        Usuario(id=1, usuario="antonio.a", password_hash=get_password_hash("Temporal-A1"), activo=True),
        Usuario(id=2, usuario="antonio.b", password_hash=get_password_hash("Temporal-B1"), activo=True),
        Usuario(id=3, usuario="club.gines", password_hash=get_password_hash("Club-pass-1"), activo=True),
        Usuario(id=4, usuario="admin", password_hash=get_password_hash("Admin-pass-1"), activo=True),
    ]
    db.add_all(users)
    db.add_all([
        UserAccount(user_id=1, account_type="ENTRENADOR", must_change_password=False, onboarding_complete=True),
        UserAccount(user_id=2, account_type="ENTRENADOR", must_change_password=False, onboarding_complete=True),
        UserAccount(user_id=3, account_type="CLUB", must_change_password=False, onboarding_complete=True),
        UserAccount(user_id=4, account_type="ADMIN", must_change_password=False, onboarding_complete=True),
    ])
    season_1 = Temporada(id=1, nombre="25/26")
    season_2 = Temporada(id=2, nombre="26/27")
    db.add_all([season_1, season_2])
    db.add_all([
        PerfilEntrenador(id=1, usuario_id=1, nombre="Antonio", apellidos="García López", temporada_actual_id=1),
        PerfilEntrenador(id=2, usuario_id=2, nombre="Antonio", apellidos="García López", temporada_actual_id=1),
    ])
    club = Club(id=1, owner_user_id=3, nombre="Gines")
    benjamin = SportsCategory(id=1, nombre="Benjamín")
    alevin = SportsCategory(id=2, nombre="Alevín")
    db.add_all([club, benjamin, alevin])
    db.add(CoachAssignment(
        id=1, coach_user_id=1, club_id=1, temporada_id=1, category_id=1,
        active=True,
    ))
    version = TaxonomiaObjetivoVersion(
        id=1, codigo_version="TEST", estado="BORRADOR", fecha_creacion="2026-08-12",
        motivo="tests", manifiesto_sha256="a" * 64, catalogo_sha256="b" * 64,
    )
    category = CategoriaObjetivo(id=10, version_id=1, codigo="TEC", nombre="Técnica", orden=1)
    objectives = [
        ObjetivoNormalizadoV2(id=10, version_id=1, categoria_id=10, nombre="Pase", orden=1, activo=True),
        ObjetivoNormalizadoV2(id=11, version_id=1, categoria_id=10, nombre="Control", orden=2, activo=True),
    ]
    db.add_all([
        version, category, *objectives,
        TipoTarea(id=1, nombre="Rondo"),
        Espacio(id=1, descripcion_original="10 x 10 metros"),
        Tiempo(id=1, descripcion_original="10 minutos"),
    ])
    official = Ejercicio(
        id=1, numero=1, codigo="OF1", nombre="Rondo oficial 4 contra 2",
        tipo_tarea_id=1, jugadores=6, espacio_id=1, tiempo_id=1,
        desarrollo="Cuatro poseedores conservan ante dos defensores.",
    )
    db.add(official)
    db.add_all([
        EjercicioObjetivoV2(ejercicio_id=1, objetivo_id=10),
        EjercicioObjetivoV2(ejercicio_id=1, objetivo_id=11),
    ])
    db.commit()
    yield db, users
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def draft(name="Rondo 4x2 con apoyos exteriores"):
    return {
        "nombre": name,
        "descripcion": "Cuatro poseedores conservan ante dos defensores con apoyos fuera.",
        "tipo_tarea_id": 1,
        "jugadores": 6,
        "espacio_id": 1,
        "tiempo_id": 1,
        "categoria_objetivo_id": 10,
        "objetivo_ids": [10, 11],
        "materiales": ["4 conos", "Balones"],
    }


def create_for_a(db, users):
    result = create_ejercicio(EjercicioCreate(**draft()), db, users[0])
    return result["exercise"].id


def test_owner_crud_and_other_trainer_is_denied(security_db):
    db, users = security_db
    exercise_id = create_for_a(db, users)
    ownership = db.get(ExerciseOwnership, exercise_id)
    assert ownership.created_by_user_id == users[0].id
    assert get_ejercicio(exercise_id, users[0], db).id == exercise_id

    updated = update_ejercicio(
        exercise_id,
        EjercicioUpdate(**draft("Rondo editado por Antonio A")),
        users[0],
        db,
    )
    assert updated.nombre == "Rondo editado por Antonio A"

    with pytest.raises(HTTPException) as read_error:
        get_ejercicio(exercise_id, users[1], db)
    assert read_error.value.status_code == 404
    for operation in (
        lambda: update_ejercicio(exercise_id, EjercicioUpdate(**draft()), users[1], db),
        lambda: delete_ejercicio(exercise_id, users[1], db),
    ):
        with pytest.raises(HTTPException) as denied:
            operation()
        assert denied.value.status_code == 403

    assert delete_ejercicio(exercise_id, users[0], db) is None
    assert db.get(ExerciseOwnership, exercise_id).deleted_at is not None
    with pytest.raises(HTTPException) as deleted:
        get_ejercicio(exercise_id, users[0], db)
    assert deleted.value.status_code == 404


def test_official_is_visible_and_immutable(security_db):
    db, users = security_db
    assert get_ejercicio(1, users[0], db).is_official is True
    assert get_ejercicio(1, users[1], db).is_official is True
    for operation in (
        lambda: update_ejercicio(1, EjercicioUpdate(**draft()), users[0], db),
        lambda: delete_ejercicio(1, users[0], db),
    ):
        with pytest.raises(HTTPException) as denied:
            operation()
        assert denied.value.status_code == 403


def test_club_reads_assigned_exercise_but_never_mutates(security_db):
    db, users = security_db
    exercise_id = create_for_a(db, users)
    club_user = users[2]
    assert can_view_exercise(db, club_user, db.get(Ejercicio, exercise_id)) is True
    detail = get_ejercicio(exercise_id, club_user, db)
    assert detail.creator_display == "Antonio García López"
    assert detail.assignment_context == "Benjamín · Gines · 25/26"
    assert detail.can_edit is False
    for operation in (
        lambda: update_ejercicio(exercise_id, EjercicioUpdate(**draft()), club_user, db),
        lambda: delete_ejercicio(exercise_id, club_user, db),
    ):
        with pytest.raises(HTTPException) as denied:
            operation()
        assert denied.value.status_code == 403


def test_equal_names_do_not_share_identity_or_private_library(security_db):
    db, users = security_db
    assert users[0].id != users[1].id
    profiles = db.query(PerfilEntrenador).order_by(PerfilEntrenador.usuario_id).all()
    assert profiles[0].nombre == profiles[1].nombre == "Antonio"
    assert profiles[0].apellidos == profiles[1].apellidos
    exercise_id = create_for_a(db, users)
    visible_a = db.query(Ejercicio).filter(visible_exercise_filter(db, users[0])).all()
    visible_b = db.query(Ejercicio).filter(visible_exercise_filter(db, users[1])).all()
    assert exercise_id in {item.id for item in visible_a}
    assert exercise_id not in {item.id for item in visible_b}


def test_season_category_are_assignments_not_identity(security_db):
    db, users = security_db
    db.add(CoachAssignment(
        coach_user_id=users[0].id, club_id=1, temporada_id=2, category_id=2,
        active=True,
    ))
    db.commit()
    assignments = db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == users[0].id
    ).all()
    assert len(assignments) == 2
    assert {item.temporada.nombre for item in assignments} == {"25/26", "26/27"}
    assert {item.category.nombre for item in assignments} == {"Benjamín", "Alevín"}
    assert db.query(Usuario).filter(Usuario.id == users[0].id).count() == 1


def test_club_can_hide_and_restore_without_deleting_data(security_db):
    db, users = security_db
    other_club_user = Usuario(
        id=5, usuario="club.otro", password_hash=get_password_hash("Club-pass-2"),
        activo=True,
    )
    db.add(other_club_user)
    db.add(UserAccount(
        user_id=5, account_type="CLUB", must_change_password=False,
        onboarding_complete=True,
    ))
    db.add(Club(id=2, owner_user_id=5, nombre="Otro club"))
    db.add(CoachAssignment(
        coach_user_id=users[0].id, club_id=2, temporada_id=2,
        category_id=2, active=True,
    ))
    training = Entrenamiento(
        usuario_id=users[0].id, temporada_id=1,
        fecha=date.today() + timedelta(days=1), hora=time(18, 30),
        nombre="Sesión visible",
    )
    db.add(training)
    db.commit()

    hidden = set_trainer_visibility(
        users[0].id, ClubTrainerVisibilityIn(visible=False), users[2], db
    )
    assert hidden == {"coach_user_id": users[0].id, "visible": False}
    db.expire_all()
    assert db.get(Usuario, users[0].id) is not None
    assert db.get(Entrenamiento, training.id) is not None
    assignment = db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == users[0].id,
        CoachAssignment.club_id == 1,
    ).one()
    assert assignment.active is True
    assert assignment.visible_in_club is False
    assert db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == users[0].id,
        CoachAssignment.club_id == 2,
    ).one().visible_in_club is True
    db.add(CoachAssignment(
        coach_user_id=users[1].id, club_id=2, temporada_id=1,
        category_id=1, active=True,
    ))
    db.commit()
    with pytest.raises(HTTPException) as other_club_denied:
        set_trainer_visibility(
            users[1].id, ClubTrainerVisibilityIn(visible=False), users[2], db
        )
    assert other_club_denied.value.status_code == 403
    assert db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == users[1].id,
        CoachAssignment.club_id == 2,
    ).one().visible_in_club is True
    payload = coordination(
        temporada_id=1, coach_user_id=None, trainer_id=None,
        desde=training.fecha, hasta=training.fecha,
        current_user=users[2], db=db,
    )
    assert payload["trainers"] == []
    assert payload["activities"] == []

    shown = set_trainer_visibility(
        users[0].id, ClubTrainerVisibilityIn(visible=True), users[2], db
    )
    assert shown == {"coach_user_id": users[0].id, "visible": True}
    payload = coordination(
        temporada_id=1, coach_user_id=users[0].id, trainer_id=None,
        desde=training.fecha, hasta=training.fecha,
        current_user=users[2], db=db,
    )
    assert payload["activities"][0]["hora"] == "18:30"


def test_club_cannot_use_admin_delete_endpoint(security_db, tmp_path):
    db, users = security_db
    with pytest.raises(HTTPException) as denied:
        admin_delete_user(
            users[0].id, users[2], db,
            LocalStorageService(tmp_path / "documents"),
        )
    assert denied.value.status_code == 403
    assert db.get(Usuario, users[0].id) is not None


def test_club_creates_new_trainer_and_assigns_it_to_own_club(security_db):
    db, users = security_db
    user_count = db.query(Usuario).count()
    assigned = create_club_trainer(
        ClubTrainerCreate(
            nombre="Laura",
            apellidos="Sánchez",
            temporada_id=2,
            categoria="Infantil de primer año",
        ),
        users[2], db,
    )
    assert assigned["user_id"] not in {user.id for user in users}
    assert assigned["temporada_id"] == 2
    assert assigned["visible"] is True
    assert assigned["usuario"] == "laura.sanchez"
    assert assigned["provisional_password"]
    assert assigned["color"] == trainer_color(assigned["user_id"])
    assert db.query(Usuario).count() == user_count + 1
    created = db.get(Usuario, assigned["user_id"])
    assert verify_password(assigned["provisional_password"], created.password_hash)
    account = db.get(UserAccount, created.id)
    assert account.account_type == "ENTRENADOR"
    assert account.must_change_password is True
    relation = db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == created.id,
        CoachAssignment.club_id == 1,
        CoachAssignment.temporada_id == 2,
    ).one()
    assert relation.active is True
    assert relation.visible_in_club is True
    assert relation.category.nombre == "Infantil de primer año"

    listed = next(
        item for item in list_trainers(2, users[2], db)
        if item["user_id"] == created.id
    )
    assert listed["provisional_password"] is None

    second = create_club_trainer(
        ClubTrainerCreate(
            nombre="Laura",
            apellidos="Sánchez",
            temporada_id=2,
            categoria="Cadete nuevo",
        ),
        users[2], db,
    )
    assert second["usuario"] == "laura.sanchez2"

    response = Response()
    login_result = auth_login(
        UsuarioLogin(
            usuario=assigned["usuario"],
            password=assigned["provisional_password"],
        ),
        response,
        db,
    )
    assert login_result.message == "Sesión iniciada correctamente"
    changed = change_provisional_password(
        ProvisionalPasswordChange(password="Definitiva-Laura-5"), created, db
    )
    assert changed["must_change_password"] is False
    assert verify_password("Definitiva-Laura-5", created.password_hash)


def test_admin_deletes_club_but_preserves_trainers_and_activity(security_db):
    db, users = security_db
    club_user = Usuario(
        id=5, usuario="club.borrar", password_hash=get_password_hash("Club-pass-3"),
        activo=True,
    )
    club = Club(id=2, owner_user_id=5, nombre="Club para borrar")
    training = Entrenamiento(
        usuario_id=users[1].id, temporada_id=1,
        fecha=date.today() + timedelta(days=3), nombre="Sesión conservada",
    )
    db.add_all([
        club_user,
        UserAccount(
            user_id=5, account_type="CLUB", must_change_password=False,
            onboarding_complete=True,
        ),
        club,
        CoachAssignment(
            coach_user_id=users[1].id, club_id=2, temporada_id=1,
            category_id=1, active=True,
        ),
        training,
    ])
    db.commit()
    training_id = training.id

    assert admin_delete_club(2, users[3], db) is None
    assert db.get(Club, 2) is None
    assert db.get(Usuario, 5) is None
    assert db.get(Usuario, users[1].id) is not None
    assert db.get(Entrenamiento, training_id) is not None
    assert db.query(CoachAssignment).filter(
        CoachAssignment.club_id == 2
    ).count() == 0


def test_club_cannot_use_admin_delete_club_endpoint(security_db):
    db, users = security_db
    with pytest.raises(HTTPException) as denied:
        admin_delete_club(1, users[2], db)
    assert denied.value.status_code == 403
    assert db.get(Club, 1) is not None


def test_admin_deletes_trainer_data_but_preserves_official_exercise(
    security_db, tmp_path,
):
    db, users = security_db
    private_id = create_for_a(db, users)
    training = Entrenamiento(
        usuario_id=users[0].id, temporada_id=1,
        fecha=date.today() + timedelta(days=1), nombre="Sesión para borrar",
    )
    match = Partido(
        usuario_id=users[0].id, temporada_id=1,
        fecha=date.today() + timedelta(days=2), rival="Rival",
        local_visitante="local",
    )
    db.add_all([training, match])
    db.commit()
    training_id = training.id
    match_id = match.id
    assert admin_delete_user(
        users[0].id, users[3], db, LocalStorageService(tmp_path / "documents")
    ) is None
    assert db.get(Usuario, users[0].id) is None
    assert db.get(Entrenamiento, training_id) is None
    assert db.get(Partido, match_id) is None
    assert db.get(Ejercicio, private_id) is None
    assert db.get(Ejercicio, 1) is not None
    with pytest.raises(HTTPException) as self_delete:
        admin_delete_user(
            users[3].id, users[3], db,
            LocalStorageService(tmp_path / "documents"),
        )
    assert self_delete.value.status_code == 403


def test_colors_and_excel_are_stable_and_use_coordination_rows(security_db):
    db, users = security_db
    assert trainer_color(users[0].id) == trainer_color(users[0].id)
    assert trainer_color(users[0].id) != trainer_color(users[1].id)
    payload = {
        "club": {"nombre": "Gines"},
        "trainers": [{
            "user_id": users[0].id, "display_name": "Antonio García López",
            "categoria": "Benjamín", "color": trainer_color(users[0].id),
        }],
        "activities": [{
            "fecha": "2026-08-13", "hora": "18:30",
            "trainer_user_id": users[0].id, "trainer": "Antonio García López",
            "categoria": "Benjamín", "type": "ENTRENAMIENTO",
            "title": "Rondo", "notes": "Carga media",
            "color": trainer_color(users[0].id),
        }],
        "planning": [],
    }
    output = _coordination_workbook(
        payload, "26/27", date(2026, 8, 10), date(2026, 8, 16)
    )
    assert output.read(2) == b"PK"


def test_onboarding_replaces_provisional_password_and_is_personal(security_db):
    db, users = security_db
    user = users[0]
    account = db.get(UserAccount, user.id)
    account.must_change_password = True
    account.onboarding_complete = False
    db.commit()
    assert verify_password("Temporal-A1", user.password_hash)
    login_response = Response()
    assert auth_login(
        UsuarioLogin(usuario=user.usuario, password="Temporal-A1"),
        login_response,
        db,
    ).message == "Sesión iniciada correctamente"
    assert user_payload(db, user)["must_change_password"] is True
    with pytest.raises(HTTPException) as pending:
        create_ejercicio(EjercicioCreate(**draft()), db, user)
    assert pending.value.status_code == 409
    result = complete_onboarding(
        OnboardingComplete(
            nombre="Antonio", apellidos="García López", password="Definitiva-A2"
        ),
        user,
        db,
    )
    assert result["must_change_password"] is False
    assert result["onboarding_complete"] is True
    assert user_payload(db, user)["must_change_password"] is False
    assert not verify_password("Temporal-A1", user.password_hash)
    assert verify_password("Definitiva-A2", user.password_hash)
    assert "password" not in result and "password_hash" not in result
    assert not hasattr(db.get(Club, 1), "password_hash")


def test_similarity_never_reveals_other_private_exercise(security_db):
    db, users = security_db
    private_id = create_for_a(db, users)
    response = similares_ejercicios(
        EjercicioCreate(**draft()),
        exclude_exercise_id=None,
        current_user=users[1],
        db=db,
    )
    hidden = [item for item in response["candidates"] if item["private_match"]]
    assert hidden
    assert len(hidden) == 1
    assert all(item["exercise_id"] is None for item in hidden)
    assert all(item["name"] is None for item in hidden)
    assert all(item["similarity"] is None for item in hidden)
    assert all(item["objectives"] == [] and item["material"] == [] for item in hidden)
    assert private_id not in {item.get("exercise_id") for item in hidden}


def test_objective_multiselect_uses_or(security_db):
    db, users = security_db
    private_id = create_for_a(db, users)
    pass_only = Ejercicio(
        numero=100, codigo="PASS", nombre="Solo pase", tipo_tarea_id=1,
        jugadores=4, espacio_id=1, tiempo_id=1,
    )
    control_only = Ejercicio(
        numero=101, codigo="CONTROL", nombre="Solo control", tipo_tarea_id=1,
        jugadores=4, espacio_id=1, tiempo_id=1,
    )
    db.add_all([pass_only, control_only])
    db.flush()
    db.add_all([
        EjercicioObjetivoV2(ejercicio_id=pass_only.id, objetivo_id=10),
        EjercicioObjetivoV2(ejercicio_id=control_only.id, objetivo_id=11),
    ])
    db.commit()
    ids = {
        row[0]
        for row in db.query(Ejercicio.id)
        .filter(exercise_taxonomy_filter(1, objetivo_v2_ids=[10, 11]))
        .all()
    }
    assert ids == {1, private_id, pass_only.id, control_only.id}


def test_admin_creates_distinct_trainer_with_provisional_access(security_db):
    db, users = security_db
    result = admin_create_trainer(
        AdminTrainerCreate(
            nombre="Antonio",
            apellidos="García López",
            usuario="antonio.tercero",
            password_provisional="Provisional-3",
            tipo="CLUB",
            club_id=1,
            temporada_id=1,
            categoria="Infantil",
        ),
        users[3],
        db,
    )
    assert result["user_id"] not in {users[0].id, users[1].id}
    created = db.get(Usuario, result["user_id"])
    assert verify_password("Provisional-3", created.password_hash)
    account = db.get(UserAccount, created.id)
    assert account.must_change_password is True
    assert account.onboarding_complete is False
    completed = complete_onboarding(
        OnboardingComplete(
            nombre="Antonio", apellidos="García López", password="Personal-Nueva-2"
        ),
        created,
        db,
    )
    assert completed["onboarding_complete"] is True
    assert not verify_password("Provisional-3", created.password_hash)


def test_admin_creates_trainer_identity_without_assignment(security_db):
    db, users = security_db
    result = admin_create_trainer(
        AdminTrainerCreate(
            nombre="Lucía", apellidos="Martín", usuario="lucia.martin",
            password_provisional="Inicial-456",
        ),
        users[3],
        db,
    )
    assert result["account_type"] == "ENTRENADOR"
    assert result["assignments"] == []
    profile = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == result["user_id"]
    ).one()
    assert profile.temporada_actual_id is None
    assert db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == result["user_id"]
    ).count() == 0


def test_admin_creates_independent_assignment(security_db):
    db, users = security_db
    result = admin_create_trainer(
        AdminTrainerCreate(
            nombre="Pedro", apellidos="López", usuario="independiente",
            password_provisional="Inicial-123", tipo="INDEPENDIENTE",
            club_id=None, temporada_id=2, categoria="Alevín",
        ), users[3], db,
    )
    assert result["account_type"] == "ENTRENADOR"
    assert result["must_change_password"] is True
    assignment = db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == result["user_id"]
    ).one()
    assert assignment.club_id is None
    assert assignment.category.nombre == "Alevín"


def test_admin_creates_club_login_and_private_password_change(security_db):
    db, users = security_db
    club = admin_create_club(
        AdminClubCreate(
            nombre_club="Club Deportivo Norte",
            usuario="club.norte",
            password_provisional="Club-Norte-123",
        ),
        users[3], db,
    )
    assert club["account_type"] == "CLUB"
    club_user = db.query(Usuario).filter(Usuario.usuario == "club.norte").one()
    assert db.query(Club).filter(Club.owner_user_id == club_user.id).one().nombre == "Club Deportivo Norte"

    response = Response()
    login_result = auth_login(
        UsuarioLogin(usuario="club.norte", password="Club-Norte-123"), response, db
    )
    assert login_result.message == "Sesión iniciada correctamente"
    assert "session=" in response.headers["set-cookie"]
    changed = change_provisional_password(
        ProvisionalPasswordChange(password="Club-Personal-456"), club_user, db
    )
    assert changed["must_change_password"] is False
    assert not verify_password("Club-Norte-123", club_user.password_hash)


def test_public_registration_routes_do_not_exist():
    paths = {route.path for route in auth_router.routes}
    assert "/api/auth/register" not in paths
    assert "/api/auth/register-club" not in paths
    assert any(
        route.path == "/api/club/entrenadores" and "POST" in route.methods
        for route in club_router.routes
    )
    assert any(
        route.path == "/api/club/coordination" and "GET" in route.methods
        for route in club_router.routes
    )
    assert not any(
        route.path == "/api/club/entrenadores/credenciales"
        for route in club_router.routes
    )
    assert not any(
        route.path == "/api/club/entrenadores/asignar" and "POST" in route.methods
        for route in club_router.routes
    )
    assert any(
        route.path == "/api/club/entrenadores/{coach_user_id}/visibilidad"
        and "PUT" in route.methods
        for route in club_router.routes
    )
    assert not any(
        route.path.startswith("/api/club/entrenadores")
        and "DELETE" in route.methods
        for route in club_router.routes
    )


def test_same_login_endpoint_authenticates_all_account_roles(security_db):
    db, users = security_db
    credentials = [
        (users[0], "Temporal-A1", "ENTRENADOR"),
        (users[2], "Club-pass-1", "CLUB"),
        (users[3], "Admin-pass-1", "ADMIN"),
    ]
    for user, password, expected_role in credentials:
        response = Response()
        result = auth_login(
            UsuarioLogin(usuario=user.usuario, password=password), response, db
        )
        assert result.message == "Sesión iniciada correctamente"
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        token = cookie["session"].value
        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/api/auth/me",
            "headers": [(b"cookie", f"session={token}".encode())],
            "query_string": b"",
            "server": ("scoutia.test", 80),
            "client": ("test", 1234),
            "scheme": "http",
        })
        authenticated_user = get_current_user(request, db)
        payload = user_payload(db, authenticated_user)
        assert payload["account_type"] == expected_role
        assert isinstance(payload["must_change_password"], bool)
        assert isinstance(payload["onboarding_complete"], bool)
        assert "session=" in response.headers["set-cookie"]

    with pytest.raises(HTTPException) as invalid:
        auth_login(
            UsuarioLogin(usuario="antonio.b", password="incorrecta"),
            Response(), db,
        )
    assert invalid.value.status_code == 401
    assert invalid.value.detail == "Usuario o contraseña incorrectos."


def test_only_admin_creates_accounts_and_club_coordination_is_read_only(security_db):
    db, users = security_db
    response = Response()
    login_result = auth_login(
        UsuarioLogin(usuario="admin", password="Admin-pass-1"), response, db
    )
    assert login_result.message == "Sesión iniciada correctamente"
    with pytest.raises(HTTPException) as denied:
        require_admin(db, users[2])
    assert denied.value.status_code == 403
    training = Entrenamiento(
        usuario_id=users[0].id, temporada_id=1, fecha=date(2030, 8, 12),
        nombre="Presión tras pérdida", duracion_minutos=75,
    )
    match = Partido(
        usuario_id=users[0].id, temporada_id=1, fecha=date(2030, 8, 13),
        rival="Rival FC", local_visitante="local",
    )
    second_training = Entrenamiento(
        usuario_id=users[1].id, temporada_id=1, fecha=date(2030, 8, 12),
        nombre="Salida de balón", duracion_minutos=60,
    )
    db.add(CoachAssignment(
        coach_user_id=users[1].id, club_id=1, temporada_id=1,
        category_id=2, active=True,
    ))
    db.add_all([training, match, second_training])
    db.add_all([
        PlanificacionDiaria(
            usuario_id=users[0].id, temporada_id=1,
            fecha=date(2030, 8, 12), nota="Nota de Antonio A",
        ),
        PlanificacionDiaria(
            usuario_id=users[1].id, temporada_id=1,
            fecha=date(2030, 8, 13), nota="Nota de Antonio B",
        ),
    ])
    db.commit()
    result = coordination(
        temporada_id=1, trainer_id=users[0].id,
        desde=date(2030, 8, 12), hasta=date(2030, 8, 13),
        current_user=users[2], db=db,
    )
    assert {item["type"] for item in result["activities"]} == {"ENTRENAMIENTO", "PARTIDO"}
    assert {item["trainer_user_id"] for item in result["activities"]} == {users[0].id}
    all_result = coordination(
        temporada_id=1, trainer_id=None,
        desde=date(2030, 8, 12), hasta=date(2030, 8, 13),
        current_user=users[2], db=db,
    )
    assert {item["trainer_user_id"] for item in all_result["activities"]} == {
        users[0].id, users[1].id,
    }
    assert len([item for item in all_result["activities"] if item["type"] == "ENTRENAMIENTO"]) == 2
    selected_by_user_id = coordination(
        temporada_id=1, coach_user_id=users[0].id,
        desde=date(2030, 8, 12), hasta=date(2030, 8, 13),
        current_user=users[2], db=db,
    )
    assert {item["trainer_user_id"] for item in selected_by_user_id["activities"]} == {
        users[0].id,
    }
    assert [item["note"] for item in selected_by_user_id["planning"]] == [
        "Nota de Antonio A",
    ]
    assert {item["note"] for item in all_result["planning"]} == {
        "Nota de Antonio A", "Nota de Antonio B",
    }
    empty_result = coordination(
        temporada_id=1, coach_user_id=users[0].id,
        desde=date(2040, 1, 1), hasta=date(2040, 1, 7),
        current_user=users[2], db=db,
    )
    assert empty_result["activities"] == []
    assert empty_result["planning"] == []
    for operation in (
        lambda: update_entrenamiento(
            training.id, EntrenamientoUpdate(nombre="Alterado"), users[2], db
        ),
        lambda: delete_entrenamiento(training.id, users[2], db),
        lambda: create_temporada(
            TemporadaCreate(nombre="No autorizada"), users[2], db
        ),
    ):
        with pytest.raises(HTTPException) as forbidden:
            operation()
        assert forbidden.value.status_code == 403


def test_new_training_and_reuse_reject_past_dates_without_touching_history(security_db):
    db, users = security_db
    past = date.today() - timedelta(days=1)
    historical = Entrenamiento(
        usuario_id=users[0].id,
        temporada_id=1,
        fecha=past,
        nombre="Histórico conservado",
    )
    db.add(historical)
    db.commit()

    with pytest.raises(HTTPException) as create_error:
        create_entrenamiento(
            EntrenamientoCreate(fecha=past, nombre="Nuevo en el pasado"),
            users[0],
            db,
        )
    assert create_error.value.status_code == 422

    with pytest.raises(HTTPException) as reuse_error:
        reutilizar_entrenamiento(
            historical.id,
            ReutilizarIn(fecha=past),
            users[0],
            db,
        )
    assert reuse_error.value.status_code == 422
    assert db.get(Entrenamiento, historical.id).nombre == "Histórico conservado"

    created_today = create_entrenamiento(
        EntrenamientoCreate(fecha=date.today(), nombre="Entrenamiento de hoy"),
        users[0],
        db,
    )
    assert created_today.fecha == date.today()


def test_past_day_accepts_note_and_calendar_exposes_it(security_db):
    db, users = security_db
    past = date.today() - timedelta(days=7)
    result = save_note(
        planning_date=past,
        data=NotaIn(contenido="Incidencia registrada después del partido"),
        temporada_id=1,
        current_user=users[0],
        db=db,
    )
    assert result.nota == "Incidencia registrada después del partido"
    calendar = get_calendario(
        year=past.year,
        month=past.month,
        temporada_id=1,
        current_user=users[0],
        db=db,
    )
    day = calendar["planificacion"][past.isoformat()]
    assert day["nota"] == "Incidencia registrada después del partido"
    assert day["entrenamientos"] == []


def test_private_image_owner_can_replace_and_remove(security_db, tmp_path, monkeypatch):
    db, users = security_db
    exercise_id = create_for_a(db, users)
    monkeypatch.setattr(ejercicios_api, "IMAGES_DIR", tmp_path)
    class AsyncUpload:
        def __init__(self, filename, data):
            self.filename = filename
            self.file = BytesIO(data)

        async def read(self, size=-1):
            return self.file.read(size)

    image = AsyncUpload("rondo.png", b"\x89PNG\r\n\x1a\nprivate-exercise-image")
    updated = asyncio.run(upload_ejercicio_image(
        exercise_id, image, users[0], db
    ))
    assert len(updated.imagenes_asociadas) == 1
    assert list(tmp_path.rglob("*.png"))

    denied_image = AsyncUpload("foreign.png", b"\x89PNG\r\n\x1a\nforeign")
    with pytest.raises(HTTPException) as denied:
        asyncio.run(upload_ejercicio_image(
            exercise_id, denied_image, users[1], db
        ))
    assert denied.value.status_code == 403

    assert delete_ejercicio_image(exercise_id, users[0], db) is None
    db.expire_all()
    assert db.get(Ejercicio, exercise_id).imagenes_asociadas == []
    assert not list(tmp_path.rglob("*.png"))
