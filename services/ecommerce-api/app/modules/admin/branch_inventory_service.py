from app.core.errors import forbidden
from app.models.customer import Customer


def check_store_inventory_permission(
    actor: Customer, target_store_id: int, target_city_id: int
) -> None:
    if actor.role == "admin":
        return
    if actor.role == "city_planner":
        if actor.city_id != target_city_id:
            raise forbidden("City planner can only manage stores in assigned city")
        return
    if actor.role == "store_manager":
        if actor.store_id != target_store_id:
            raise forbidden("Store manager can only update own store inventory")
        return
    raise forbidden("No inventory edit permission")
