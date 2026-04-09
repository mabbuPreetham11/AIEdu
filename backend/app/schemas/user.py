from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool

