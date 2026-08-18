import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.services.router import tool_router

def test_routing_safe_tool():
    # Web research is read-only and should execute automatically
    res = tool_router.validate_action("web_research", {})
    assert res["allowed"] is True
    assert res["requires_approval"] is False

def test_routing_consequential_tool():
    # Checkout requires user approval
    res = tool_router.validate_action("prepare_checkout", {"item": "table"})
    assert res["allowed"] is True
    assert res["requires_approval"] is True

def test_routing_payment_blocked():
    # Payments are HIGH_RISK and must be blocked from automation
    res = tool_router.validate_action("execute_payment", {"amount": 100})
    assert res["allowed"] is False
    assert res["manual_action_required"] is True
    assert "HIGH RISK" in res["reason"]

def test_routing_unregistered_tool():
    res = tool_router.validate_action("unregistered_tool_xyz", {})
    assert res["allowed"] is False
    assert "not registered" in res["reason"]
