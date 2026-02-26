from __future__ import annotations

from dataclasses import dataclass

from .conflict import ConflictBlock

_SYSTEM_PROMPT = """\
You are an expert software engineer specializing in resolving Git merge conflicts.

When given a merge conflict your job is to produce a single merged version of the
code that satisfies the intent of BOTH sides. Follow these rules strictly:

1. Preserve the functionality of both sides wherever possible.
2. If both sides make compatible changes, combine them intelligently.
3. If the changes are logically incompatible — meaning they cannot both work
   correctly at the same time — respond with CANNOT_RESOLVE and a clear,
   developer-friendly explanation of why.
4. Do not add explanatory comments to the output code. Output only the resolved code.
5. Respond using EXACTLY one of the two formats below — nothing else:

   RESOLVED:
   <resolved code here>

   or:

   CANNOT_RESOLVE:
   <clear explanation of why the conflict cannot be automatically resolved>
"""


@dataclass
class ResolutionResult:
    resolved: bool
    content: str       # the merged code, or empty string on failure
    explanation: str   # brief summary always present


class AIResolver:
    def __init__(self, api_key: str, model: str = "claude-opus-4-6") -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def resolve(
        self,
        conflict: ConflictBlock,
        language: str = "",
    ) -> ResolutionResult:
        """Ask the AI to resolve a single *conflict* block."""
        language_hint = f" The file is written in {language}." if language else ""

        user_message = (
            f"Resolve the following Git merge conflict.{language_hint}\n\n"
            f"--- OURS ({conflict.ours_label}) ---\n"
            f"{conflict.ours}\n"
            f"--- THEIRS ({conflict.theirs_label}) ---\n"
            f"{conflict.theirs}"
        )

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        if not response.content:
            return ResolutionResult(
                resolved=False,
                content="",
                explanation="API returned an empty response.",
            )
        return _parse_response(response.content[0].text)


def _parse_response(text: str) -> ResolutionResult:
    """Parse the raw model response into a :class:`ResolutionResult`."""
    text = text.strip()

    if text.startswith("RESOLVED:"):
        content = text[len("RESOLVED:"):].strip()
        return ResolutionResult(
            resolved=True,
            content=content,
            explanation="Conflict resolved successfully.",
        )

    if text.startswith("CANNOT_RESOLVE:"):
        explanation = text[len("CANNOT_RESOLVE:"):].strip()
        return ResolutionResult(
            resolved=False,
            content="",
            explanation=explanation,
        )

    # Graceful fallback: treat the entire response as resolved code.
    return ResolutionResult(
        resolved=True,
        content=text,
        explanation="Conflict resolved.",
    )
