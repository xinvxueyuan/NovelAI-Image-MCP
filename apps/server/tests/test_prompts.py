"""Tests for the `novelai_*` prompt templates."""

from __future__ import annotations

from typing import Any


class TestPromptTemplates:
    async def test_prompts_are_registered(self, mcp_client: Any) -> None:
        prompts = {prompt.name for prompt in await mcp_client.list_prompts()}
        assert prompts == {"novelai_prompt_writer", "novelai_image_workflow"}

    async def test_prompt_arguments_are_published(self, mcp_client: Any) -> None:
        by_name = {p.name: p for p in await mcp_client.list_prompts()}
        writer = by_name["novelai_prompt_writer"]
        arguments = {arg.name: arg for arg in (writer.arguments or [])}
        assert set(arguments) == {"idea", "style"}
        assert arguments["style"].required is False
        workflow = by_name["novelai_image_workflow"]
        assert [arg.name for arg in (workflow.arguments or [])] == ["goal"]

    async def test_prompt_writer_renders_the_idea(self, mcp_client: Any) -> None:
        result = await mcp_client.get_prompt(
            "novelai_prompt_writer", {"idea": "a lighthouse at dusk", "style": "ink"}
        )
        text = result.messages[0].content.text
        assert "a lighthouse at dusk" in text
        assert "ink" in text
        # The template must point at the tools that carry the workflow.
        assert "generate_image" in text
        assert "suggest_tags" in text

    async def test_workflow_prompt_lists_the_tool_order(self, mcp_client: Any) -> None:
        result = await mcp_client.get_prompt(
            "novelai_image_workflow", {"goal": "a poster from a sketch"}
        )
        text = result.messages[0].content.text
        assert "a poster from a sketch" in text
        for tool in ("generate_image", "annotate_image", "inpaint", "upscale_image"):
            assert tool in text
