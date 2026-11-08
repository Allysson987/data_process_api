
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CaseResponse(BaseModel):
    id: str
    case_number: str
    court: str | None
    case_class: str | None
    subject: str | None
    is_sealed: bool
    is_public: bool

    model_config = ConfigDict(from_attributes=True)
