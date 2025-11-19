from fastapi import APIRouter

router = APIRouter()

@router.post("/seed-admin")
def seed_admin_user():
    """Seed the database with admin user for initial setup"""
    try:
        from gc_registry.seed import seed_admin
        seed_admin()
        return {"message": "Admin user seeded successfully"}
    except Exception as e:
        return {"error": str(e)}