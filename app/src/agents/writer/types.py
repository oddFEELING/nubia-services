"""
This module contains shared types and dependencies for the story agents.
"""

from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class StoryAgentDependencies():
    """Dependencies required by story agents"""
    story_id: str
    project_id: str
    analysis_id: Optional[str] = None
 

class ConversationSummaryReturn(BaseModel):
    """Return type for analysis conversation summary"""
    content: str = Field(
        description="A comprehensive and detailed summary of the findings of the analysis.",
        min_length=100,  # Ensure meaningful content
        max_length=500,  # Reasonable limit for display
    )

class StoryResult(BaseModel):
    """Return type for story agents"""
    content: str = Field(
        description="The story content",
        min_length=1
    )
    actions_taken: List[str] = Field(
        description="List of actions taken during story generation",
        examples=[
            ["Retrieved analysis conversation"],
            ["Generated story content"]
        ]
    )


class ChatReturnType(BaseModel):
    """Return type for the chat rendering on the front end"""
    content: str = Field(
        description="Main content (response) of the chat message which is a conversation between the user and the agent. Must be very expressive and valid markdown string. Properly formatted markdown is recommended.",
        min_length=1000,  # Ensure meaningful content
        max_length=5000,  # Reasonable limit for display
    )
    options: List[str] = Field(
        description="A list of strings that are very short actionable options/suggestions that the user can choose from.",
        examples=[
            ["Rewrite Story", "Summarize Story"],
            ["Export Story", "Try different story angle"]
        ]
    )


__all__ = ["StoryAgentDependencies", "ChatReturnType", "StoryResult"]
