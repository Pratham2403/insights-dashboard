"""
Tests for the FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import json
from app.utils.state_manager import generate_conversation_id


client = TestClient(app)


def test_health_endpoint():
    """
    Test the health endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint():
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "documentation" in response.json()
    assert "health" in response.json()


def test_chat_endpoint():
    """
    Test the chat endpoint.
    """
    # Create a test message
    conversation_id = generate_conversation_id()
    request_data = {
        "conversation_id": conversation_id,
        "message": "I am the owner of Samsung and I want to know about the Customer Insights about my products."
    }
    
    response = client.post("/api/v1/chat", json=request_data)
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert "conversation_id" in response_data
    assert "messages" in response_data
    assert "user_requirements" in response_data
    assert "current_step" in response_data
    
    # Check that the conversation includes both the user message and assistant response
    messages = response_data["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_mock_search_endpoint():
    """
    Test the mock search endpoint.
    """
    request_data = {
        "query": "Samsung S25 Ultra",
        "limit": 5
    }
    
    response = client.post("/api/v1/mock-search", json=request_data)
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert "results" in response_data
    assert len(response_data["results"]) <= 5
