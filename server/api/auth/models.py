from pydantic import BaseModel


class UserInfo(BaseModel):
    sub: str
    email: str = ""
    name: str = ""
    roles: list[str] = []

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def is_engineer(self) -> bool:
        return "engineer" in self.roles or self.is_admin

    @property
    def is_field_worker(self) -> bool:
        return "field_worker" in self.roles or self.is_engineer


class TokenInfo(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
