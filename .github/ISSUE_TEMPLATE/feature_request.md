---
name: ✨ Feature request
description: Suggest a new tool, parameter, or behavior
title: "✨ feat: <brief summary>"
labels: ["enhancement", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for the suggestion! Tell us what you'd like and why.
  - type: textarea
    id: problem
    attributes:
      label: The problem
      description: What can't you do today, or what's painful about how it works now?
      placeholder: "I'm frustrated when ..."
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: Proposed solution
      description: What new tool / parameter / behavior would fix it?
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Other approaches you've considered and why they don't fit.
    validations:
      required: false
  - type: textarea
    id: context
    attributes:
      label: Additional context
      description: Screenshots, links to NovelAI docs, related issues, or anything else useful.
    validations:
      required: false
