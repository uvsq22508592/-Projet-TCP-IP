from dataclasses import dataclass, field
from typing import Any


@dataclass
class SharedFile:
    """Metadata published by a peer for one shared file."""

    name: str
    description: str = ""
    relative_path: str = ""
    size: int = 0

    def as_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "relative_path": self.relative_path,
            "size": self.size,
        }


@dataclass
class PeerInfo:
    """Connection and publication state tracked by the central server."""

    host: str
    port: int
    last_seen: float
    files: list[dict[str, Any]] = field(default_factory=list)
