from pydantic import BaseModel


class OrganizationDetailsResponse(BaseModel):
    name: str
    logo: str
    favicon: str
    title: str | None