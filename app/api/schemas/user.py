# app/api/schemas/user.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.user_model import UserRole


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=12)
    confirm_password: str = Field(..., min_length=12)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponseData(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type prefix")


class LoginResponse(BaseModel):
    success: bool = Field(default=True, description="Indicates api operation status")
    message: str = Field(default="Login successful", description="Response message")
    data: LoginResponseData


class LogoutResponse(BaseModel):
    success: bool = Field(default=True, description="Indicates api operation status")
    message: str = Field(default="Logout successful", description="Response message")


class RefreshResponseData(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type prefix")
    expires_in: int = Field(
        ..., description="Token lifetime in seconds", examples=[3600]
    )


class RefreshResponse(BaseModel):
    success: bool = Field(default=True, description="Indicates api operation status")
    message: str = Field(default="Refresh successful", description="Response message")
    data: RefreshResponseData
