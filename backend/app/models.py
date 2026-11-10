import uuid
from datetime import UTC, datetime

from pydantic import EmailStr, computed_field
from sqlalchemy import CheckConstraint, Column, Enum
from sqlmodel import Field, Relationship, SQLModel

from app.core.authorization import (
    EffectiveRole,
    Permission,
    UserRole,
    effective_role,
    permissions_for,
)


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    role: UserRole | None = Field(
        default=None,
        sa_column=Column(
            Enum(
                UserRole,
                native_enum=False,
                values_callable=lambda enum: [role.value for role in enum],
                length=16,
            ),
            nullable=True,
        ),
    )
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    role: UserRole | None = UserRole.MEMBER
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    model_config = SQLModel.model_config.copy()
    model_config["extra"] = "forbid"
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    role: UserRole | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    model_config = SQLModel.model_config.copy()
    model_config["extra"] = "forbid"
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    __table_args__ = (
        CheckConstraint("role IN ('manager', 'member')", name="ck_user_role"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    items: list[Item] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class CurrentUserPublic(UserPublic):
    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_role(self) -> EffectiveRole:
        return effective_role(self)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def capabilities(self) -> list[Permission]:
        return sorted(permissions_for(self))


class MetricsPublic(SQLModel):
    message: str = "Metrics preview"
    active_projects: int = 0


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: uuid.UUID


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
