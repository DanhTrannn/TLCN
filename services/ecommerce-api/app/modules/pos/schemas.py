from pydantic import BaseModel, ConfigDict, Field


class POSTItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    variant_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=999)


class POSTransactionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    store_id: int = Field(gt=0)
    items: list[POSTItemRequest] = Field(min_length=1)
    payment_method: str = Field(pattern=r"^(cash|card)$")
    amount_received_vnd: int | None = Field(default=None, ge=0)


class POSTItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: int
    product_name: str
    sku: str
    size_code: str
    color_code: str
    unit_price_vnd: int
    quantity: int
    line_total_vnd: int


class POSTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    order_number: str
    status: str
    channel: str
    store_id: int
    payment_method: str
    items: list[POSTItemResponse]
    subtotal_vnd: int
    total_vnd: int
    created_at: str


class POSProductSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    variant_id: int
    product_name: str
    sku: str
    size_code: str
    color_code: str
    price_vnd: int
    store_stock: int
    global_stock: int
