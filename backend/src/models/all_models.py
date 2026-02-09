import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlmodel import JSON, Field, Relationship, SQLModel


def generate_uuid() -> str:
    return str(uuid.uuid4())


# Enums
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    PROMPT = "prompt"
    WORKFLOW = "workflow"
    AGENT = "agent"


class StepType(str, Enum):
    AI = "ai"
    LOGIC = "logic"
    VERIFICATION = "verification"
    APPROVAL = "approval"
    CONDITION = "condition"


# Core Models
class Organization(SQLModel, table=True):
    __tablename__ = "organizations"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    users: list["User"] = Relationship(back_populates="organization")


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    email: str = Field(unique=True)
    organization_id: str | None = Field(default=None, foreign_key="organizations.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization | None = Relationship(back_populates="users")


# Knowledge Base
class DataSource(SQLModel, table=True):
    __tablename__ = "data_sources"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    type: str  # s3, sharepoint, manual
    connection_config: dict = Field(default={}, sa_column=Column(JSON))
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    documents: list["Document"] = Relationship(back_populates="data_source")


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    filename: str
    file_path: str  # MinIO path (original file)
    pdf_preview_path: str | None = None  # PDF path for PPTX preview
    file_type: str | None = None
    file_size: int | None = None
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    parsing_job_id: str | None = None
    error_message: str | None = None
    metadata_: dict = Field(default={}, sa_column=Column("metadata", JSON))

    data_source_id: str | None = Field(default=None, foreign_key="data_sources.id")
    thread_id: str | None = Field(default=None, foreign_key="conversations.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    data_source: DataSource | None = Relationship(back_populates="documents")
    conversation: Optional["Conversation"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Document.thread_id==Conversation.id",
            "foreign_keys": "[Document.thread_id]",
        }
    )


# Chat
class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str | None = None
    user_id: str | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    messages: list["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id")
    role: str  # user, assistant
    content: str
    sources: list[dict] = Field(default=[], sa_column=Column(JSON))
    citations: list[dict] = Field(default=[], sa_column=Column(JSON))
    thinking_steps: list[dict] = Field(default=[], sa_column=Column(JSON))
    reasoning_events: list[dict] = Field(default=[], sa_column=Column(JSON))
    agent_transitions: list[dict] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Conversation = Relationship(back_populates="messages")


# Agents & Workflows
class Agent(SQLModel, table=True):
    __tablename__ = "agents"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    description: str | None = None
    instructions: str | None = None
    model: str = Field(default="claude-3-sonnet-20240229")
    tools: list[str] = Field(default=[], sa_column=Column(JSON))

    type: AgentType = Field(default=AgentType.AGENT)
    position_x: int = Field(default=0)
    position_y: int = Field(default=0)
    config: dict = Field(default={}, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    steps: list["AgentStep"] = Relationship(back_populates="agent")


class AgentStep(SQLModel, table=True):
    __tablename__ = "agent_steps"
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    agent_id: str = Field(foreign_key="agents.id")
    name: str
    step_type: StepType = Field(default=StepType.AI)
    order: int
    config: dict = Field(default={}, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent: Agent = Relationship(back_populates="steps")
