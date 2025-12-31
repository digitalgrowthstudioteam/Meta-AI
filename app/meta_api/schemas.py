from pydantic import BaseModel


class MetaConnectResponse(BaseModel):
    redirect_url: str
