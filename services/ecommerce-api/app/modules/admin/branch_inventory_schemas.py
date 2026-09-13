from pydantic import BaseModel, ConfigDict, Field


class BranchInventoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    store_id: int
    store_name: str
    city_id: int
    city_name: str
    variant_id: int
    variant_sku: str
    size_code: str
    color_code: str
    price_vnd: int
    on_hand: int
    opening_on_hand: int


class UpdateStockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_id: int = Field(gt=0)
    variant_id: int = Field(gt=0)
    on_hand: int = Field(ge=0)
