import re
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, StringConstraints

# Characters people commonly type inside a phone number.
_PHONE_SEPARATORS = re.compile(r"[\s\-().]")


def normalise_phone(value: str) -> str:
    """Reduce a phone number to digits only, e.g. "+91 98765-43210" -> "919876543210".

    This is the format the seed data uses and the format the incoming
    message webhook matches against, so every teacher's number is stored
    the same way no matter how it was typed.
    """
    phone = _PHONE_SEPARATORS.sub("", value).removeprefix("+")

    # E.164 allows at most 15 digits, country code included.
    if not phone.isascii() or not phone.isdigit() or not 8 <= len(phone) <= 15:
        raise ValueError(
            "Phone must be 8 to 15 digits including the country code, "
            "for example 919876543210"
        )

    return phone


class BaseTeacher(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    phone: Annotated[str, AfterValidator(normalise_phone)]
    cohort_id: UUID


class TeacherCreate(BaseTeacher):
    """Teacher details to create teacher"""


class TeacherRead(BaseModel):
    id: UUID
    name: str
    phone: str
    cohort_id: UUID
