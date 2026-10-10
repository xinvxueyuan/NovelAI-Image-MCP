"""MCP prompt templates that script the NovelAI image workflow.

Prompts are user-invoked templates: a client lists them and renders one with
its arguments, then receives the text as a message. They encode the house style
for prompting this server, so an agent does not have to rediscover it.
"""

from __future__ import annotations

from .server import mcp


@mcp.prompt(
    title="Write a NovelAI prompt",
    description=(
        "Turn a plain-language idea into a NovelAI-style tag prompt plus a "
        "negative prompt and generation settings."
    ),
    tags={"novelai", "prompting"},
)
def novelai_prompt_writer(idea: str, style: str = "") -> str:
    """Draft a NovelAI prompt for ``idea`` (optionally in a given ``style``)."""
    style_line = style.strip() or "unspecified"
    return (
        "Write a prompt for NovelAI Diffusion image generation.\n"
        "\n"
        f"Idea: {idea}\n"
        f"Style or mood: {style_line}\n"
        "\n"
        "Produce, in this order:\n"
        "1. A comma-separated tag prompt: subject first, then composition, "
        "lighting, medium and quality tags. Keep the most specific tags early.\n"
        "2. A negative prompt for anatomy, artefacts and unwanted framing.\n"
        "3. Suggested settings (model id, width, height, steps, scale, sampler) "
        "chosen from the novelai://models and novelai://samplers resources.\n"
        "4. Character prompts (with x/y centres) if the scene has more than one "
        "subject.\n"
        "\n"
        "Then call generate_image with the result. Use suggest_tags first if any "
        "tag vocabulary is uncertain, and check the cost with "
        "estimate_anlas_cost before large or batched runs."
    )


@mcp.prompt(
    title="Plan a NovelAI image workflow",
    description=(
        "Lay out the tool sequence (txt2img, ControlNet, img2img, inpaint, "
        "upscale) that reaches a described goal."
    ),
    tags={"novelai", "workflow"},
)
def novelai_image_workflow(goal: str) -> str:
    """Plan the tool sequence that achieves ``goal``."""
    return (
        "Plan a NovelAI image workflow for this goal:\n"
        f"{goal}\n"
        "\n"
        "Walk through the steps in order, naming the tool for each one and the "
        "arguments that matter:\n"
        "1. Recon: get_subscription for the Anlas balance, novelai://models and "
        "novelai://samplers for the vocabulary.\n"
        "2. Prompting: suggest_tags, then generate_image (text-to-image).\n"
        "3. Structure (optional): annotate_image to build a ControlNet condition "
        "from an existing picture for a later pass.\n"
        "4. Refinement: image_to_image for restyling, inpaint to redraw a region.\n"
        "5. Finishing: director_tool (lineart, sketch, bg-removal, colorize...), "
        "then upscale_image.\n"
        "\n"
        "For each step state what to inspect in the result before continuing, and "
        "flag the steps that spend Anlas."
    )


__all__ = ["novelai_image_workflow", "novelai_prompt_writer"]
