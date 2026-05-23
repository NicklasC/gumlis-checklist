from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.checklist import Checklist, CommonGroup

class BaseRepository(ABC):
    @abstractmethod
    def get_all_checklists(self) -> List[Checklist]:
        """Retrieve all active and archived checklists."""
        pass

    @abstractmethod
    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        """Retrieve a specific checklist by ID."""
        pass

    @abstractmethod
    def save_checklist(self, checklist: Checklist) -> None:
        """Save or update a checklist in storage."""
        pass

    @abstractmethod
    def delete_checklist(self, checklist_id: str) -> None:
        """Delete a checklist permanently."""
        pass

    @abstractmethod
    def get_all_common_groups(self) -> List[CommonGroup]:
        """Retrieve all common re-add template groups."""
        pass

    @abstractmethod
    def save_common_group(self, group: CommonGroup) -> None:
        """Save or update a common template group."""
        pass

    @abstractmethod
    def delete_common_group(self, group_id: str) -> None:
        """Delete a common template group permanently."""
        pass
