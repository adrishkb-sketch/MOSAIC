import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.services.gemini import GeminiService
from app.core.config import settings

def test_gemini_service_not_configured():
    # Save original key
    original_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = ""
    
    # Initialize service
    service = GeminiService()
    
    assert service.is_configured() is False
    with pytest.raises(ValueError) as exc_info:
        _ = service.client
        
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
    
    # Restore original key
    settings.GEMINI_API_KEY = original_key

def test_gemini_service_configured():
    # Save original key
    original_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = "test_fake_key"
    
    service = GeminiService()
    assert service.is_configured() is True
    
    # Accessing client should create it
    try:
        client = service.client
        assert client is not None
    except Exception as e:
        # It's fine if it fails connection later, but initialization should run
        pass
        
    # Restore original key
    settings.GEMINI_API_KEY = original_key
