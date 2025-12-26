from fastapi import APIRouter
import sys
sys.path.insert(0, '../../..')

from immo_core.data import get_selectable_locations, get_location_defaults

from ..schemas import LocationDefaults

router = APIRouter(prefix="/data", tags=["data"])

@router.get("/locations")
async def get_locations():
    return {"locations": get_selectable_locations()}

@router.get("/location-defaults/{location}", response_model=LocationDefaults)
async def get_defaults(location: str):
    defaults = get_location_defaults(location)
    return LocationDefaults(**defaults)