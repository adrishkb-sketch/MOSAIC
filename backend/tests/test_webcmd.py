import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.services.webcmd import webcmd_client

def test_webcmd_browser_lifecycle():
    # 1. Create session
    session_id = webcmd_client.create_session()
    assert session_id is not None
    assert session_id.startswith("session_")
    
    try:
        # 2. Run script (navigate to example.com)
        res = webcmd_client.run_script(
            session_id=session_id,
            script='await page.goto("https://example.com"); return await page.title();'
        )
        assert res.get("ok") is True
        assert res.get("result") == "Example Domain"
        
        # 3. Get accessibility snapshot
        snapshot = webcmd_client.get_accessibility_snapshot(session_id)
        assert "Example Domain" in snapshot
        
        # 4. Get screenshot
        screenshot_data = webcmd_client.get_screenshot(session_id)
        assert screenshot_data is not None
        assert screenshot_data.startswith("data:image/png;base64,")
        
    finally:
        # 5. Close session
        webcmd_client.close_session(session_id)
