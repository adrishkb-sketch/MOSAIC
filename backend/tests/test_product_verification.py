import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.services.gemini import gemini_service, VerifiedCatalogItem, VerifiedCatalogResponse
from app.services.webcmd import webcmd_client
from app.services.agent import agent_orchestrator, active_sessions

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    for table in reversed(Base.metadata.sorted_tables):
        with engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()

def test_clean_and_verify_items_filters_junk_and_compare():
    raw_items = [
        {"title": "Add to Compare", "price": "", "url": "/compare"},
        {"title": "Compare", "price": "", "url": "/compare-2"},
        {"title": "Acer Nitro V 15 Intel Core i5 13th Gen (16GB/512GB SSD/RTX 4050)", "price": "₹69,990", "specs": "Intel i5 13th Gen | RTX 4050", "url": "/acer-nitro-v"},
        {"title": "Sponsored", "price": "", "url": "/ad"},
        {"title": "Lenovo LOQ Intel Core i5 12th Gen (16GB/512GB SSD/RTX 3050)", "price": "₹62,490", "specs": "Intel i5 12th Gen | RTX 3050", "url": "/lenovo-loq"}
    ]

    # Test fallback deterministic cleaning
    with patch.object(gemini_service, "is_configured", return_value=False):
        cleaned = agent_orchestrator._clean_and_verify_items(
            user_query="mid range gaming laptops",
            page_title="Gaming Laptops",
            current_url="https://www.flipkart.com/search?q=gaming+laptop",
            raw_items=raw_items
        )
        assert len(cleaned) == 2
        assert cleaned[0]["title"] == "Acer Nitro V 15 Intel Core i5 13th Gen (16GB/512GB SSD/RTX 4050)"
        assert "69,990" in cleaned[0]["description"]
        assert cleaned[1]["title"] == "Lenovo LOQ Intel Core i5 12th Gen (16GB/512GB SSD/RTX 3050)"

def test_clean_and_verify_items_gemini_integration():
    raw_items = [
        {"title": "Add to Compare", "price": "", "url": "/compare"},
        {"title": "Acer Nitro V 15 Intel Core i5", "price": "₹69,990", "url": "/acer-nitro-v"}
    ]

    mock_verified = VerifiedCatalogResponse(
        items=[
            VerifiedCatalogItem(
                id="1",
                title="Acer Nitro V 15 Intel Core i5 13th Gen (RTX 4050)",
                price="₹69,990",
                specs_or_details="16GB RAM | 512GB SSD | 6GB RTX 4050",
                url="https://www.flipkart.com/acer-nitro-v",
                selector="a[href='/acer-nitro-v']"
            )
        ],
        summary="Found top-rated mid-range gaming laptop matching your criteria."
    )

    with patch.object(gemini_service, "is_configured", return_value=True), \
         patch.object(gemini_service, "verify_and_clean_catalog_items", return_value=mock_verified):
        
        cleaned = agent_orchestrator._clean_and_verify_items(
            user_query="mid range gaming laptops",
            page_title="Gaming Laptops - Flipkart",
            current_url="https://www.flipkart.com/search?q=gaming+laptop",
            raw_items=raw_items
        )

        assert len(cleaned) == 1
        assert cleaned[0]["title"] == "Acer Nitro V 15 Intel Core i5 13th Gen (RTX 4050)"
        assert "₹69,990" in cleaned[0]["description"]
        assert "RTX 4050" in cleaned[0]["description"]
        assert "Compare" not in cleaned[0]["title"]

def test_mid_range_query_preservation():
    email = "user_midrange@example.com"
    task_id = "test_midrange_task"

    # Test that typing a specific search query while awaiting user choice routes to search
    active_sessions[task_id] = {
        "session_id": "dummy_sess",
        "email": email,
        "request": "suggest laptops",
        "status": "asking",
        "state": "awaiting_user_choice",
        "current_url": None,
        "steps": [],
        "available_options": [
            {"id": "1", "title": "Entry Level Gaming Laptops", "description": "Budget options"},
            {"id": "2", "title": "Mid Range Gaming Laptops", "description": "RTX 4050/4060"}
        ],
        "browser_active": False
    }

    with patch.object(gemini_service, "is_configured", return_value=False), \
         patch.object(webcmd_client, "navigate_to", return_value={"ok": True}), \
         patch.object(webcmd_client, "run_script", return_value={"ok": True, "result": [
             {"text": "Acer Nitro V 15 Gaming Laptop ₹69,990", "href": "https://www.flipkart.com/acer"}
         ]}), \
         patch.object(webcmd_client, "get_screenshot", return_value="data:image/png;base64,mock"):

        response = client.post(
            "/api/agent/chat",
            json={"email": email, "message": "mid range gaming laptops", "task_id": task_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] is not None
        assert len(data["results"]) > 0
        # Verify that search url searched for user's query and didn't fall back to Entry Level
        assert "mid+range+gaming+laptops" in data.get("browser_url", "") or "mid range gaming laptops" in data.get("response", "").lower()
