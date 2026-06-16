from pydantic import BaseModel
class Organization(BaseModel):
    organization_name: str
    login_email: str
    password: str