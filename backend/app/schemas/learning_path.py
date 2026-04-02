from pydantic import BaseModel, Field


class LearningPathBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    difficulty: str = Field(..., min_length=1)
    estimated_hours: int = Field(..., gt=0)
    icon: str | None = None
    order_index: int = Field(..., ge=0)


class LearningPathCreate(LearningPathBase):
    pass


class LearningPathUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    difficulty: str | None = Field(default=None, min_length=1)
    estimated_hours: int | None = Field(default=None, gt=0)
    icon: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class LearningPath(LearningPathBase):
    id: int
    created_at: str
