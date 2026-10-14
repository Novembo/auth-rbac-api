def test_register_creates_user_with_role_user(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "motdepasse123"})
    assert r.status_code == 201
    assert r.json()["role"] == "user"
    assert "hashed_password" not in r.json()


def test_cannot_choose_role_at_registration(client):
    r = client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "motdepasse123", "role": "admin"},
    )
    assert r.json()["role"] == "user"


def test_duplicate_email_is_rejected(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "motdepasse123"})
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "autremotdepasse"})
    assert r.status_code == 400


def test_password_too_short_is_rejected(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "court"})
    assert r.status_code == 422


def test_login_returns_jwt(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "motdepasse123"})
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "motdepasse123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert len(r.json()["access_token"]) > 20


def test_login_with_wrong_password_is_rejected(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "motdepasse123"})
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "mauvais"})
    assert r.status_code == 401


def test_login_with_unknown_email_gives_same_error(client):
    r1 = client.post("/auth/login", json={"email": "inconnu@example.com", "password": "motdepasse123"})
    client.post("/auth/register", json={"email": "a@example.com", "password": "motdepasse123"})
    r2 = client.post("/auth/login", json={"email": "a@example.com", "password": "mauvais"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


def test_me_requires_a_valid_token(client, make_user):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer faux-jeton"}).status_code == 401

    _, headers, email = make_user()
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == email
