import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.models import User
from backend.auth import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create test user
    db = TestingSessionLocal()
    user = User(
        email="valid@example.com",
        name="Valid User",
        hashed_password=get_password_hash("secret123")
    )
    db.add(user)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


# CT-LOGIN-001: Logando com email e senha válidos
def test_ct_login_001_valid_email_password():
    response = client.post(
        "/api/auth/login",
        json={"email": "valid@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "valid@example.com"

    # Verify protected route with returned token
    token = data["access_token"]
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "valid@example.com"


def test_ct_login_001_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        json={"email": "valid@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Credenciais inválidas" in response.json()["detail"]


# CT-LOGIN-002: Logando com credenciais do Google
@patch("backend.auth.id_token.verify_oauth2_token")
def test_ct_login_002_google_oauth(mock_verify_google):
    # Mock successful google token verification
    mock_verify_google.return_value = {
        "sub": "google-uid-12345",
        "email": "googleuser@example.com",
        "name": "Google User"
    }

    response = client.post(
        "/api/auth/google",
        json={"credential_token": "mocked-valid-google-id-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "googleuser@example.com"

    # Verify token access to protected endpoint
    token = data["access_token"]
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "googleuser@example.com"


@patch("backend.auth.id_token.verify_oauth2_token")
def test_ct_login_002_invalid_google_token(mock_verify_google):
    mock_verify_google.side_effect = ValueError("Invalid token")

    response = client.post(
        "/api/auth/google",
        json={"credential_token": "invalid-token"}
    )
    assert response.status_code == 401
    assert "Token do Google inválido" in response.json()["detail"]
