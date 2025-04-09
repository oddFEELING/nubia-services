import pytest 
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from src.agents.writer.base import (
    ModelType,
    Agent,
    RunContext,
    StoryAgent,
    ChatReturnType,
    ConversationSummaryReturn,
    project_file_list,
    get_analysis_conversation,
    get_nodes,
    parse_files,
    describe_csv,
    StoryAgentDependencies,

)

# #####
# ## This file contains mock tests for the StoryAgent. simply run pytest -vs test_story_agent.py in the test directory

# #####

class TestStoryAgent:

    @patch("src.agents.writer.base.Agent")
    def test_agent_initialization(self, mock_agent_class):
        #Create instance of mock agent
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        #Setup tools
        mock_agent_instance.tool.return_value = lambda func: func

        #Create StoryAgent
        model = "openai:gpt-4o"
        agent = StoryAgent(model)

        #make assertions
        mock_agent_class.assert_called_once()
        assert agent.model == model

        assert mock_agent_instance.tool.call_count == 5
