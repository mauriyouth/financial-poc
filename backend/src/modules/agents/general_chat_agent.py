"""General Chat agent for non-specialized queries."""

from google.adk.agents import LlmAgent

from src.connectors.google_adk_connector import GoogleADKConnector
from src.connectors.opensearch_connector import OpenSearchConnector
from src.core.logging import logger
from src.modules.agents.base_agent import BaseAgent
from src.modules.agents.tools.retrieval_tool import create_retrieval_tool
from src.modules.embeddings.gemini_embedder import GeminiEmbedder
from src.stores.opensearch.chunk_store import ChunkStore


class GeneralChatAgent(BaseAgent):
    """General purpose chat agent for non-specialized queries."""

    def __init__(
        self,
        adk_connector: GoogleADKConnector,
        opensearch_connector: OpenSearchConnector,
        embedder: GeminiEmbedder,
    ) -> None:
        """
        Initialize General Chat agent.

        Args:
            adk_connector: Google ADK connector instance
            opensearch_connector: OpenSearch connector
            embedder: Embedder instance
        """
        super().__init__(
            name="general_chat_agent",
            description="General purpose assistant for conversational queries and general questions",
        )
        self.adk_connector = adk_connector
        self.opensearch_connector = opensearch_connector
        self.embedder = embedder
        logger.info("GeneralChatAgent initialized")

    def get_agent_definition(self) -> LlmAgent | None:
        """Create the General Chat agent definition."""
        instruction = """You are a helpful and knowledgeable assistant with access to a document search tool.

Your role:
- Answer questions about uploaded documents and data sources
- Provide explanations and clarifications based on retrieved information
- Help users understand document content
- Redirect specialized financial or SEC questions to note that dedicated agents handle those

## CRITICAL RULE: STRICT GROUNDING REQUIREMENT

**You should primarily provide information that you can cite with a chunk ID from the retrieval tool.**

However, you may use the summaries provided in "Available Documents" context for high-level overviews or when the user asks specifically for a summary of the file itself, WITHOUT needing specific chunk citations for the summary content.

When responding:
1. **Check "Available Documents" context**: You may receive summaries of available documents in your context. Use these freely to answer general questions like "What is this file about?".
2. **Use the retrieval tool for Details**: For specific facts, figures, or claims, you MUST use the retrieval tool and provide citations.
3. **NEVER make up or infer information** - only state what is explicitly in the retrieved chunks or the provided summaries.
4. **Specific findings MUST include a citation** using the format {{cite:chunk_id}}
5. **STRICT RULE**: You MUST ONLY use chunk IDs that were returned by the retrieval tool in the current turn. DO NOT invent IDs. DO NOT use IDs from previous turns unless re-retrieved.
6. **If the retrieval tool returns no results** and the summary is insufficient, clearly state: "I could not find relevant information."
7. **Do NOT answer from general knowledge** when discussing uploaded documents

## How to handle document questions:

**User asks: "What is this document about?" or "Summarize this file"**
1. comprehensive answer based on the "Available Documents" summary provided in your context.
2. You do NOT need citations for this high-level summary.

**User asks: "What does it say about X?"**
1. Use retrieval tool with query about X
2. If found: Quote or paraphrase with citations {{cite:chunk_id}}
3. If not found: "I did not find information about X in the document."

## Citation format for RETRIEVED content:
- Place {{cite:chunk_id}} immediately after each cited fact or statement
- Multiple citations: "The document states X {{cite:abc123}} and Y {{cite:def456}}."
- If a paragraph draws from one source, cite at the end

## Example response format:
"The document is a financial report covering Q3 performance (based on document summary). Specifically, revenue increased by 20% {{cite:chunk1}} and operating costs decreased {{cite:chunk2}}."

**Remember: If it's a specific detail, CITE IT. If it's a general summary of the file, you can use the provided context.**"""

        # Create retrieval tool
        # Ensure index exists
        self.opensearch_connector.create_chunks_index()
        chunk_store = ChunkStore(self.opensearch_connector)
        retrieval_tool = create_retrieval_tool(chunk_store, self.embedder)

        return self.adk_connector.create_llm_agent(
            name=self.name,
            description=self.description,
            instruction=instruction,
            temperature=0.7,
            tools=[retrieval_tool],
        )
