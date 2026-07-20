from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ChecklistItem(BaseModel):
    id: str
    title: str
    is_checked: bool = False
    category: str = "Övrigt"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    completed_at: Optional[str] = None

class Checklist(BaseModel):
    id: str
    title: str
    is_template: bool = False
    category_order: List[str] = Field(default_factory=lambda: ["Att göra", "Hem", "Inköp", "Planering", "Övrigt"])
    last_cleaned_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    items: List[ChecklistItem] = Field(default_factory=list)

class CommonGroup(BaseModel):
    id: str
    name: str
    items: List[str] = Field(default_factory=list)

class ChecklistsData(BaseModel):
    checklists: List[Checklist] = Field(default_factory=list)
    common_groups: List[CommonGroup] = Field(default_factory=list)
