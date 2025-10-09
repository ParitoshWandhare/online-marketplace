from fastapi.testclient import TestClient
from vision_ai.vision_service import app

client = TestClient(app)

def test_generate_story():
    with open("sample.jpg", "rb") as f:
        response = client.post("/generate_story", files={"image": ("sample.jpg", f, "image/jpeg")})
    assert response.status_code == 200
    assert "description" in response.json()