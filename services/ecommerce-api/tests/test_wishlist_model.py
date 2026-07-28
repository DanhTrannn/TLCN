from app.models.wishlist import WishlistItem


def test_wishlist_table_has_required_invariant_indexes() -> None:
    table = WishlistItem.__table__
    indexes = {index.name: index for index in table.indexes}

    assert indexes["uq_wishlist_items_customer_id_product_id"].unique is True
    assert "ix_wishlist_items_updated_at_wishlist_item_id" in indexes
    assert {column.name for column in table.primary_key.columns} == {"wishlist_item_id"}
