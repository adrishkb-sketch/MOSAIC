import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.main import app
from app.db.session import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    for table in reversed(Base.metadata.sorted_tables):
        with engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()

def test_memory_api_lifecycle():
    email = "api_test@example.com"
    
    # 1. Add memory
    response = client.post(
        f"/api/memory/items?email={email}",
        json={
            "key": "skills",
            "value": "Python, ML",
            "classification": "PRIVATE_USER_DATA",
            "source": "explicit"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "skills"
    assert data["value"] == "Python, ML"
    memory_id = data["id"]
    
    # 2. List memories
    response = client.get(f"/api/memory/items?email={email}")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["key"] == "skills"
    
    # 3. Get single memory
    response = client.get(f"/api/memory/items/{memory_id}")
    assert response.status_code == 200
    item = response.json()
    assert item["key"] == "skills"
    
    # 4. Get why explanation
    response = client.get(f"/api/memory/items/{memory_id}/why")
    assert response.status_code == 200
    why = response.json()
    assert why["key"] == "skills"
    assert why["shared_with_others"] is False
    assert why["added_to_global_knowledge"] is False
    
    # 5. Update memory
    response = client.put(
        f"/api/memory/items/{memory_id}",
        json={"value": "Python, C++, ML"}
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["value"] == "Python, C++, ML"
    
    # 6. Delete memory
    response = client.delete(f"/api/memory/items/{memory_id}")
    assert response.status_code == 200
    
    # 7. List should be empty
    response = client.get(f"/api/memory/items?email={email}")
    assert len(response.json()) == 0
