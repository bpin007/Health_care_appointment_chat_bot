# backend/api/calendly_integration.py

from fastapi import APIRouter, HTTPException, Query
from models.schemas import AppointmentRequest, AvailabilityResponse
from tools.availability_tool import AvailabilityTool
from tools.booking_tool import BookingTool
from models.schemas import TimeSlot

router = APIRouter()
availability = AvailabilityTool()
booking_tool = BookingTool()

@router.get("/doctors")
def get_doctors(
    date: str = Query(...),
    appointment_type: str = Query(...),
):
    """
    Returns doctors who:
    - Match specialization required
    - Work on that date
    """
    try:
        # Will internally find relevant doctors
        slots = availability.check(date, appointment_type)

        # unique doctors
        doctors = []
        seen = set()

        for slot in slots:
            d_id = slot["doctor_id"]
            if d_id not in seen:
                doctors.append({
                    "doctor_id": slot["doctor_id"],
                    "name": slot["doctor_name"],
                    "specialization": slot["specialization"],
                    "rating": 4.7,  # static now
                    "image": f"https://ui-avatars.com/api/?name={slot['doctor_name'].replace(' ', '+')}"
                })
                seen.add(d_id)

        return {"doctors": doctors}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/availability", response_model=AvailabilityResponse)
def get_availability(date: str, appointment_type: str):
    try:
        slots_raw = availability.check(date, appointment_type)

        slots = [TimeSlot(**slot) for slot in slots_raw]

        return {"date": date, "available_slots": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
def book(payload: AppointmentRequest):
    try:
        result = booking_tool.book(payload.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: str):
    try:
        result = booking_tool.cancel(booking_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
