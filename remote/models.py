"""Input models for the MCP tools. The Field descriptions are read by the
model calling the tool, so they carry instructions, not just types."""
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    email: str = Field(description="The HR or careers address")
    company: str | None = Field(default=None, description="Company it belongs to")
    source_url: str | None = Field(
        default=None,
        description=(
            "The exact page URL where you saw this address. Required. If you did "
            "not see it on a page, do not submit it."
        ),
    )


class Application(BaseModel):
    to: str = Field(description="Recipient address")
    subject: str = Field(description="Subject line")
    body: str = Field(description="Plain text body, written for this company specifically")
    company: str | None = Field(default=None)
    source_url: str | None = Field(
        default=None, description="Page URL where the address was found"
    )
