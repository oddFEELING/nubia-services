import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import asyncio

from src.routes.agent_router import agent_router, StoryAgent, run_story_agent, BackgroundTasks, StoryAgentRouteBody, get_story_details


# #####
# ## This file contains mock tests for the StoryAgent API endpoint via FastAPI. simply run pytest -vs test_agent_api.py in the test directory

# #####


client = TestClient(agent_router)

@pytest.mark.asyncio
@patch("src.tools.story_details.get_story_details")
@patch("src.routes.agent_router.run_story_agent")
async def test_story_agent_endpoint(mock_run_story_agent, mock_get_story_details):

    mock_get_story_details.return_value = [{"story_id": "story_456", "projectId": "pr1234"}]

    mock_run_story_agent.return_value = None

    # Define test request body
    test_body = {
        "story_id": "story_456",
        "model": "openai:gpt-4o",
        "prompt": "Create a story based on the News Pdf file"
    }

    #Make request
    response = client.post("/story/chat", json=test_body)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    mock_get_story_details.assert_called_once_with("story_456")