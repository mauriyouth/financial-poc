"""Verification agent to check and fix hallucinations."""

from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.core.logging import logger
from src.modules.agents.base_agent import BaseAgent


class VerificationAgent(BaseAgent):
    """Agent that verifies and corrects citations in responses."""

    def __init__(self, adk_connector: GoogleADKConnector) -> None:
        """
        Initialize Verification agent.

        Args:
            adk_connector: Google ADK connector instance
        """
        super().__init__(
            name="verification_agent",
            description="Verifies citations and corrects hallucinations",
        )
        self.adk_connector = adk_connector
        logger.info("VerificationAgent initialized")

    def get_agent_definition(self) -> LlmAgent | None:
        """Create the Verification agent definition."""
        instruction = """You are a meticulous fact-checking assistant.

Your Task:
Verify the citations in a draft response against the provided Reference Content (Verified Chunks).

Inputs:
1. User Query
2. Draft Response (with citations in {{cite:uuid}} format)
3. Reference Content (Verified Chunks) - This contains the actual text content for each valid Chunk ID.

Rules:
1. **Check every citation**: Scan the Draft Response for {{cite:uuid}} tags.
2. **Retrieve Content**: Look up the text content for that UUID in the Reference Content.
   - If the UUID is missing from Reference Content -> INVALID CITATION.
3. **Verify Claim**: Read the text content associated with the UUID. Does it support the claim made in the Draft Response?
   - If the text DOES NOT support the claim -> HALLUCINATION.
   - If the text supports the claim -> VALID.

Action:
- If ALL citations are valid AND support their claims: Return the Draft Response exactly as is.
- If ANY citation is invalid (missing ID or hallucinated content):
  - REWRITE the sentence to correct the claim based ONLY on the provided Reference Content.
  - If the claim is unsupported by any provided chunk, remove the claim or state "Information not found in retrieved context."
  - Maintain the {{cite:uuid}} format for valid citations.
  - DO NOT invent new content.
  - DO NOT invent new citations.

Output:
- Return ONLY the corrected response text.
- Do not add conversational filler like "Here is the corrected version".
"""

        return self.adk_connector.create_llm_agent(
            name=self.name,
            description=self.description,
            instruction=instruction,
            # Use a low temperature for deterministic verification
            temperature=0.0,
        )
