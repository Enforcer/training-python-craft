from pydantic import BaseModel, ConfigDict


class PlanDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    description: str
