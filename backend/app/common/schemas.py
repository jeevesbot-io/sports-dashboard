"""
Common Pydantic schemas and response models.
"""
from typing import TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

DataT = TypeVar('DataT')


class StandardResponse(BaseModel, Generic[DataT]):
    """Standard API response wrapper."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[DataT] = None
    errors: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    database: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and limit."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated response wrapper."""
    
    items: list[DataT]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: list[DataT],
        total: int,
        pagination: PaginationParams
    ) -> "PaginatedResponse[DataT]":
        """Create paginated response."""
        pages = (total + pagination.limit - 1) // pagination.limit
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )