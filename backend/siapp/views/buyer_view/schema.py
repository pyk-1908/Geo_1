from ninja import Schema
from pydantic import Field

product_id_example = "15,31"
buyer_id_example = 1


class BuyerBuyerMapRequest(Schema):
    country_id: str = Field(
        ...,
        description="Numeric IDs of the countries (comma-separated)",
        example="64,65"
    )
    product_id: str = Field(
        ...,
        description="Unique identifiers of the products (comma-separated)",
        example=product_id_example
    )

    class Config:
        json_schema_extra = {
            "example": {
                "country_id": "64",
                "product_id": product_id_example,
            }
        }
