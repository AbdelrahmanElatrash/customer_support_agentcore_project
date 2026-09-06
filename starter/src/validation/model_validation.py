from pydantic import BaseModel, Field, field_validator


class Request(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    customer_id: str | None = None
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("message cannot be empty.")

        return value


class Response(BaseModel):
    response: str