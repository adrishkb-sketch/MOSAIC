import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.models import UserMemory
from app.services.agent import active_sessions
from app.services.gemini import BrowserNextAction, InteractiveOption

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    for table in reversed(Base.metadata.sorted_tables):
        with engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()

def test_active_browser_sorting_does_not_trigger_google_search():
    email = "flipkart_user@example.com"

    # Start live site automation on Flipkart
    response = client.post(
        "/api/agent/chat",
        json={"email": email, "message": "apply_for: https://www.flipkart.com/search?q=laptop"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["browser_active"] is True
    assert "flipkart" in (data.get("browser_url") or "").lower()
    task_id = data["task_id"]

    # In active browsing mode, ask to find the cheapest one
    response2 = client.post(
        "/api/agent/chat",
        json={"email": email, "message": "find the cheapest one", "task_id": task_id}
    )
    assert response2.status_code == 200
    data2 = response2.json()

    # Verify that the agent stayed in the browser and did NOT reset to Google Search
    assert data2["browser_active"] is True
    assert "google.com/search" not in (data2.get("browser_url") or "").lower()
    assert "cheapest" in data2["response"].lower() or "price" in data2["response"].lower() or "option" in data2["response"].lower()

def test_gemini_step_reasoning_loop():
    email = "gemini_reasoning_user@example.com"
    task_id = "test_gemini_task_123"

    # Setup active session
    active_sessions[task_id] = {
        "session_id": "dummy_session",
        "email": email,
        "request": "Buy a book on Flipkart",
        "status": "browsing",
        "state": "idle",
        "current_url": "https://www.flipkart.com/books",
        "steps": [],
        "available_options": [],
        "browser_active": True
    }

    mock_action = BrowserNextAction(
        thought="Filtered the catalog to display the lowest priced books first.",
        action_type="click",
        selector="div._10UF8M",
        click_text="Price -- Low to High"
    )

    with patch("app.services.gemini.gemini_service.is_configured", return_value=True), \
         patch("app.services.gemini.gemini_service.determine_next_browser_action", return_value=mock_action), \
         patch("app.services.webcmd.webcmd_client.click_element", return_value=True), \
         patch("app.services.webcmd.webcmd_client.extract_page_details", return_value={"url": "https://www.flipkart.com/books", "title": "Books", "items": [{"title": "Book A", "price": "199", "url": "/book-a"}]}), \
         patch("app.services.webcmd.webcmd_client.get_screenshot", return_value="data:image/png;base64,mock"):

        response = client.post(
            "/api/agent/chat",
            json={"email": email, "message": "filter the cheapest", "task_id": task_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["browser_active"] is True
        assert "Filtered the catalog" in data["response"]
