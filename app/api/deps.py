from app.services.skkni_service import SkkniService

def get_skkni_service() -> SkkniService:
    """Provide SkkniService via FastAPI Depends."""
    return SkkniService()
