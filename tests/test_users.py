"""Tests for User CRUD endpoints.

Every test asserts both the HTTP status code and the APIResponse envelope
shape to ensure consistent API contract.
"""

from uuid import uuid4

from httpx import AsyncClient

from app.config import get_settings

settings = get_settings()
USERS_URL = f"{settings.API_V1_PREFIX}/users"


def _valid_user_payload(suffix: str = "") -> dict:
    """Generate a valid user creation payload."""
    return {
        "email": f"test{suffix}@example.com",
        "username": f"testuser{suffix}",
        "password": "SecurePass1",
    }


def _assert_envelope(body: dict, success: bool = True) -> None:
    """Assert the APIResponse envelope structure."""
    assert "success" in body
    assert body["success"] is success
    assert "data" in body
    assert "message" in body


# ── Create User ──────────────────────────────────────────────────────────────


async def test_create_user_returns_201(client: AsyncClient) -> None:
    """POST /users should return 201 with a valid payload."""
    payload = _valid_user_payload("_create")
    response = await client.post(USERS_URL, json=payload)
    body = response.json()

    assert response.status_code == 201
    _assert_envelope(body, success=True)
    assert body["data"]["email"] == payload["email"]
    assert body["data"]["username"] == payload["username"]
    assert "id" in body["data"]
    assert "hashed_password" not in body["data"]


async def test_create_user_duplicate_email_returns_409(client: AsyncClient) -> None:
    """POST /users with a duplicate email should return 409."""
    payload = _valid_user_payload("_dup_email")
    await client.post(USERS_URL, json=payload)

    # Attempt to create another user with the same email but different username
    payload2 = {**payload, "username": "different_user"}
    response = await client.post(USERS_URL, json=payload2)

    assert response.status_code == 409
    body = response.json()
    _assert_envelope(body, success=False)


async def test_create_user_duplicate_username_returns_409(client: AsyncClient) -> None:
    """POST /users with a duplicate username should return 409."""
    payload = _valid_user_payload("_dup_username")
    await client.post(USERS_URL, json=payload)

    # Attempt to create another user with the same username but different email
    payload2 = {**payload, "email": "different@example.com"}
    response = await client.post(USERS_URL, json=payload2)

    assert response.status_code == 409
    body = response.json()
    _assert_envelope(body, success=False)


async def test_create_user_invalid_password_returns_422(client: AsyncClient) -> None:
    """POST /users with a short password should return 422."""
    payload = _valid_user_payload("_bad_pw")
    payload["password"] = "short"  # Too short, no digit
    response = await client.post(USERS_URL, json=payload)

    assert response.status_code == 422
    body = response.json()
    _assert_envelope(body, success=False)


# ── Get User ─────────────────────────────────────────────────────────────────


async def test_get_user_returns_200(client: AsyncClient) -> None:
    """GET /users/{id} should return 200 for an existing user."""
    # Create a user first
    payload = _valid_user_payload("_get")
    create_response = await client.post(USERS_URL, json=payload)
    user_id = create_response.json()["data"]["id"]

    response = await client.get(f"{USERS_URL}/{user_id}")
    body = response.json()

    assert response.status_code == 200
    _assert_envelope(body, success=True)
    assert body["data"]["id"] == user_id


async def test_get_user_not_found_returns_404(client: AsyncClient) -> None:
    """GET /users/{id} should return 404 for a non-existent user."""
    fake_id = str(uuid4())
    response = await client.get(f"{USERS_URL}/{fake_id}")

    assert response.status_code == 404
    body = response.json()
    _assert_envelope(body, success=False)


# ── List Users ───────────────────────────────────────────────────────────────


async def test_list_users_returns_paginated_response(client: AsyncClient) -> None:
    """GET /users should return a paginated response envelope."""
    response = await client.get(USERS_URL)
    body = response.json()

    assert response.status_code == 200
    _assert_envelope(body, success=True)
    assert "items" in body["data"]
    assert "total" in body["data"]
    assert "page" in body["data"]
    assert "page_size" in body["data"]
    assert "pages" in body["data"]


async def test_list_users_pagination_params(client: AsyncClient) -> None:
    """GET /users with pagination params should respect page and page_size."""
    response = await client.get(USERS_URL, params={"page": 1, "page_size": 2})
    body = response.json()

    assert response.status_code == 200
    _assert_envelope(body, success=True)
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 2


# ── Update User ──────────────────────────────────────────────────────────────


async def test_update_user_returns_200(client: AsyncClient) -> None:
    """PATCH /users/{id} should return 200 with updated data."""
    # Create a user first
    payload = _valid_user_payload("_update")
    create_response = await client.post(USERS_URL, json=payload)
    user_id = create_response.json()["data"]["id"]

    update_data = {"username": "updated_user"}
    response = await client.patch(f"{USERS_URL}/{user_id}", json=update_data)
    body = response.json()

    assert response.status_code == 200
    _assert_envelope(body, success=True)
    assert body["data"]["username"] == "updated_user"


async def test_update_user_partial_fields(client: AsyncClient) -> None:
    """PATCH /users/{id} should only update provided fields."""
    # Create a user first
    payload = _valid_user_payload("_partial")
    create_response = await client.post(USERS_URL, json=payload)
    user_data = create_response.json()["data"]
    user_id = user_data["id"]

    # Only update email, leave username unchanged
    update_data = {"email": "newemail@example.com"}
    response = await client.patch(f"{USERS_URL}/{user_id}", json=update_data)
    body = response.json()

    assert response.status_code == 200
    _assert_envelope(body, success=True)
    assert body["data"]["email"] == "newemail@example.com"
    assert body["data"]["username"] == user_data["username"]


# ── Delete User ──────────────────────────────────────────────────────────────


async def test_delete_user_returns_204(client: AsyncClient) -> None:
    """DELETE /users/{id} should return 204 for an existing user."""
    # Create a user first
    payload = _valid_user_payload("_delete")
    create_response = await client.post(USERS_URL, json=payload)
    user_id = create_response.json()["data"]["id"]

    response = await client.delete(f"{USERS_URL}/{user_id}")
    assert response.status_code == 204


async def test_delete_user_not_found_returns_404(client: AsyncClient) -> None:
    """DELETE /users/{id} should return 404 for a non-existent user."""
    fake_id = str(uuid4())
    response = await client.delete(f"{USERS_URL}/{fake_id}")

    assert response.status_code == 404
    body = response.json()
    _assert_envelope(body, success=False)
