"""
Pydantic models for Infrahub webhook payloads.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AttributeChange(BaseModel):
    """Represents a changed attribute in the changelog."""

    kind: str
    name: str
    value: Any
    value_previous: Any | None = None
    value_update_status: str = "added"
    properties: dict[str, Any] = Field(default_factory=dict)


class RelationshipChange(BaseModel):
    """Represents a changed relationship in the changelog."""

    name: str
    peer_id: str | None = None
    peer_kind: str | None = None
    peer_id_previous: str | None = None
    peer_kind_previous: str | None = None
    peer_status: str = "added"
    cardinality: str = "one"
    properties: dict[str, Any] = Field(default_factory=dict)


class Changelog(BaseModel):
    """Changelog containing all changes to a node."""

    node_id: str
    node_kind: str
    display_label: str = ""
    attributes: dict[str, AttributeChange] = Field(default_factory=dict)
    relationships: dict[str, RelationshipChange] = Field(default_factory=dict)


class WebhookData(BaseModel):
    """Data section of the webhook payload."""

    kind: str
    action: str
    node_id: str
    fields: list[str] = Field(default_factory=list)
    changelog: Changelog | None = None


class WebhookPayload(BaseModel):
    """Complete webhook payload from Infrahub."""

    id: str
    event: str
    branch: str
    data: WebhookData
    account_id: str
    occured_at: datetime

    def is_ticket_created(self) -> bool:
        """Check if this is a ticket created event."""
        return (
            self.event == "infrahub.node.created"
            and self.data.kind == "NetautoServiceNowTicket"
        )

    def get_attribute_value(self, attr_name: str) -> Any | None:
        """Get the value of an attribute from the changelog."""
        if self.data.changelog and attr_name in self.data.changelog.attributes:
            return self.data.changelog.attributes[attr_name].value
        return None

    @property
    def ritm(self) -> str | None:
        """Get the RITM value from the changelog."""
        return self.get_attribute_value("ritm")

    @property
    def cat_item(self) -> str | None:
        """Get the cat_item value from the changelog."""
        return self.get_attribute_value("cat_item")

    @property
    def short_description(self) -> str | None:
        """Get the short_description from the changelog."""
        return self.get_attribute_value("short_description")
