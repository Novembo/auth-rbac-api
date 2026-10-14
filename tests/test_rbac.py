def test_user_only_sees_own_resources(client, make_user):
    _, alice_headers, _ = make_user("alice@example.com")
    _, bob_headers, _ = make_user("bob@example.com")

    client.post("/resources", json={"title": "Note d'Alice", "content": "secret"}, headers=alice_headers)
    client.post("/resources", json={"title": "Note de Bob", "content": "autre secret"}, headers=bob_headers)

    alice_sees = client.get("/resources", headers=alice_headers).json()
    assert len(alice_sees) == 1
    assert alice_sees[0]["title"] == "Note d'Alice"


def test_editor_sees_all_resources(client, make_user, make_editor):
    _, alice_headers, _ = make_user("alice@example.com")
    client.post("/resources", json={"title": "Note d'Alice", "content": "x"}, headers=alice_headers)

    _, editor_headers, _ = make_editor("editor2@example.com")
    seen = client.get("/resources", headers=editor_headers).json()
    assert any(r["title"] == "Note d'Alice" for r in seen)


def test_user_cannot_edit_someone_elses_resource(client, make_user):
    _, alice_headers, _ = make_user("alice@example.com")
    _, bob_headers, _ = make_user("bob@example.com")

    created = client.post("/resources", json={"title": "A", "content": "x"}, headers=alice_headers).json()
    r = client.put(f"/resources/{created['id']}", json={"title": "Piraté", "content": "x"}, headers=bob_headers)
    assert r.status_code == 403


def test_only_admin_can_delete(client, make_user, make_editor, make_admin):
    _, alice_headers, _ = make_user("alice@example.com")
    created = client.post("/resources", json={"title": "A", "content": "x"}, headers=alice_headers).json()

    _, editor_headers, _ = make_editor("editor3@example.com")
    assert client.delete(f"/resources/{created['id']}", headers=editor_headers).status_code == 403

    _, admin_headers, _ = make_admin("admin3@example.com")
    assert client.delete(f"/resources/{created['id']}", headers=admin_headers).status_code == 204


def test_only_admin_can_list_users(client, make_user, make_admin):
    _, user_headers, _ = make_user("alice@example.com")
    assert client.get("/users", headers=user_headers).status_code == 403

    _, admin_headers, _ = make_admin("admin4@example.com")
    r = client.get("/users", headers=admin_headers)
    assert r.status_code == 200
    assert any(u["email"] == "alice@example.com" for u in r.json())


def test_admin_can_promote_a_user(client, make_user, make_admin):
    _, user_headers, email = make_user("alice@example.com")
    user_id = client.get("/auth/me", headers=user_headers).json()["id"]

    _, admin_headers, _ = make_admin("admin5@example.com")
    r = client.patch(f"/users/{user_id}/role", json={"role": "editor"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["role"] == "editor"


def test_admin_cannot_change_own_role(client, make_admin):
    admin_token, admin_headers, email = make_admin("admin6@example.com")
    admin_id = client.get("/auth/me", headers=admin_headers).json()["id"]
    r = client.patch(f"/users/{admin_id}/role", json={"role": "user"}, headers=admin_headers)
    assert r.status_code == 400


def test_role_downgrade_takes_effect_immediately_even_with_old_token(client, make_user, make_admin):
    """Le rôle est relu en base à chaque requête (require_role), donc même
    un jeton émis avant la rétrogradation perd immédiatement ses droits."""
    _, admin_headers, _ = make_admin("admin7@example.com")

    token, editor_token_headers, email = make_user("future-editor@example.com")
    user_id = client.get("/auth/me", headers=editor_token_headers).json()["id"]
    client.patch(f"/users/{user_id}/role", json={"role": "editor"}, headers=admin_headers)

    # Ce header utilise le jeton émis AVANT la promotion.
    before_promotion_headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/resources", headers=before_promotion_headers)
    assert r.status_code == 200  # le jeton reste valide, le rôle est relu en base

    client.patch(f"/users/{user_id}/role", json={"role": "user"}, headers=admin_headers)
    r = client.get("/users", headers=before_promotion_headers)
    assert r.status_code == 403  # redevenu "user" : accès admin refusé malgré le vieux jeton
