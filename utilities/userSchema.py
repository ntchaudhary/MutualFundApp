from pydantic import BaseModel
from fastapi import Form

class AuthDetails(BaseModel):
    account_id: str
    profile: str
    password: str

    @classmethod
    def as_form(
        cls,
        account_id: str = Form(...),
        profile: str = Form(...),
        password: str = Form(...)
    ):
        return cls(
            account_id=account_id,
            profile=profile,
            password=password
            )