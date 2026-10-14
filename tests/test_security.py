def test_unknown_role_is_rejected_by_schema(client, make_admin):
    _, admin_headers, _ = make_admin("admin8@example.com")
    r = client.post("/auth/register", json={"email": "x@example.com", "password": "motdepasse123"})
    user_id = r.json()["id"]
    r = client.patch(f"/users/{user_id}/role", json={"role": "superadmin"}, headers=admin_headers)
    assert r.status_code == 422


def test_deactivated_user_is_rejected_at_login(client, make_user):
    import sys
    from tests.conftest import TestingSessionLocal
    from app import models

    _, headers, email = make_user("inactif@example.com")
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    user.is_active = 0
    db.commit()
    db.close()

    r = client.post("/auth/login", json={"email": email, "password": "motdepasse123"})
    assert r.status_code == 403


def test_cors_only_allows_configured_origin(client):
    r = client.options(
        "/resources",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in r.headers
