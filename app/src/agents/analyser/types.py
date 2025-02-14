"""
This module contains shared types and dependencies for the analyser agents.
"""

from dataclasses import dataclass
from typing import List

from pydantic import BaseModel, Field


@dataclass
class AnalyserAgentDependencies:
    """Dependencies required by analyser agents"""
    project_id: str
    analysis_id: str


class AnalyzerResult(BaseModel):
    """Return type for analyzer agents"""
    content: str = Field(
        description="The analysis result or content",
        min_length=1
    )
    actions_taken: List[str] = Field(
        description="List of actions taken during analysis",
        examples=[
            ["Retrieved project files", "Analyzed CSV structure", "Generated summary"],
            ["Retrieved PDF content", "Extracted key information", "Compiled findings"]
        ]
    )


class ChatReturnType(BaseModel):
    """Return type for the chat rendering on the front end"""
    content: str = Field(
        description="Main content (response) of the chat message which is a conversation between the user and the agent. Must be very expressive and valid markdown string. Properly formatted markdown is recommended.",
        min_length=10,  # Ensure meaningful content
        max_length=4000,  # Reasonable limit for display
    )
    options: List[str] = Field(
        description="A list of strings that are very short actionable options/suggestions that the user can choose from.",
        examples=[
            ["Analyze CSV data", "Review PDF content", "Generate visualization"],
            ["View summary", "Create chart", "Export results", "Try different analysis"]
        ]
    )


__all__ = ["AnalyserAgentDependencies", "ChatReturnType", "AnalyzerResult"]
