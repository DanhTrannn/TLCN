import pytest
from pydantic import ValidationError

from app.modules.admin.schemas import (
    CreateProductRequest,
    UpdateProductRequest,
    UpdateVariantRequest,
)


def test_create_product_rejects_duplicate_variant_combination() -> None:
    with pytest.raises(ValidationError):
        CreateProductRequest(
            category_code="ao",
            slug="ao-test",
            name="Áo test",
            variants=[
                {"sku": "SKU-1", "size_code": "M", "color_code": "black", "price_vnd": 100, "opening_on_hand": 1},
                {"sku": "SKU-2", "size_code": "M", "color_code": "BLACK", "price_vnd": 100, "opening_on_hand": 1},
            ],
        )


def test_product_patch_rejects_null_name() -> None:
    with pytest.raises(ValidationError):
        UpdateProductRequest(name=None)


def test_variant_patch_requires_a_change() -> None:
    with pytest.raises(ValidationError):
        UpdateVariantRequest()


def test_variant_patch_rejects_unknown_inventory_mutation() -> None:
    with pytest.raises(ValidationError):
        UpdateVariantRequest(restock_quantity=10)
