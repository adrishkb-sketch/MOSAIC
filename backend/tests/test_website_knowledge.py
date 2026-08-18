import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.db.session import Base
from app.services.website_knowledge import website_knowledge_service
from app.db.models import SharedWebsite

# Setup memory database
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_value_sanitization():
    # Test email sanitization
    email_res = website_knowledge_service.sanitize_value("Please send details to test@example.com.")
    assert "test@example.com" not in email_res
    assert "<user_email>" in email_res

    # Test phone number sanitization
    phone_res = website_knowledge_service.sanitize_value("Contact: +1 555-0199 for verification.")
    assert "555-0199" not in phone_res
    assert "<user_phone>" in phone_res

def test_actions_sanitization_against_profile():
    profile = {
        "name": "Adrish",
        "skills": "Python, React",
        "email": "adrish@mosaic.com"
    }

    actions = [
        {"action_type": "fill", "selector": "#name", "value": "Adrish"},
        {"action_type": "fill", "selector": "#email", "value": "adrish@mosaic.com"},
        {"action_type": "fill", "selector": "#skills", "value": "Python, React"},
        {"action_type": "fill", "selector": "#budget", "value": "4000"}  # General value, shouldn't change
    ]

    sanitized = website_knowledge_service.sanitize_actions(actions, profile)
    
    assert sanitized[0]["value"] == "<name>"
    assert sanitized[1]["value"] == "<email>"
    assert sanitized[2]["value"] == "<skills>"
    assert sanitized[3]["value"] == "4000"

def test_learn_workflow(db):
    domain = "test-portal.com"
    name = "Test Job Portal"
    workflow_name = "apply_flow"
    actions = [
        {"action_type": "click", "description": "Click apply button"}
    ]
    commands = ["webcmd test-portal apply"]

    # Learn workflow
    website = website_knowledge_service.learn_workflow(
        db=db,
        domain=domain,
        name=name,
        workflow_name=workflow_name,
        actions=actions,
        commands=commands
    )

    assert website.id is not None
    assert website.domain == domain
    assert "apply_flow" in website.workflows
    assert "test-portal apply" in website.commands
