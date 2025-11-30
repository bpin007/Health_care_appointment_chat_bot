import json
from pathlib import Path
import time
import uuid

class BookingTool:
    DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "booking.json"

    def _load_bookings(self):
        if not self.DATA_PATH.exists():
            return []
        try:
            with open(self.DATA_PATH, "r") as f:
                data = f.read().strip()
                return json.loads(data) if data else []
        except:
            return []

    def _save_bookings(self, bookings):
        with open(self.DATA_PATH, "w") as f:
            json.dump(bookings, f, indent=2)

    def book(self, payload):
        bookings = self._load_bookings()

        booking_id = f"APPT-{int(time.time())}"
        confirmation_code = uuid.uuid4().hex[:6].upper()

        new_booking = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "status": "confirmed",
            "date": payload["date"],
            "start_time": payload["start_time"],
            "appointment_type": payload["appointment_type"],
            "patient_name": payload["patient_name"],
            "patient_email": payload["patient_email"],
            "patient_phone": payload["patient_phone"],
            "reason": payload["reason"],
            "doctor_id": payload.get("doctor_id"),
        }

        bookings.append(new_booking)
        self._save_bookings(bookings)

        return new_booking
    
    def cancel(self, booking_id: str):
        bookings = self._load_bookings()

        for b in bookings:
            if b["booking_id"] == booking_id:
                if b["status"] == "cancelled":
                    return {
                        "message": "Already cancelled",
                        "booking_id": booking_id,
                        "status": "cancelled"
                    }
                b["status"] = "cancelled"
                self._save_bookings(bookings)
                return {
                    "booking_id": booking_id,
                    "status": "cancelled",
                    "message": "Appointment cancelled successfully."
                }

        raise ValueError("Booking not found")

    def get_booking_by_confirmation(self, code: str):
        """Retrieve booking by confirmation or booking id"""
        bookings = self._load_bookings()
        for b in bookings:
            if b["confirmation_code"] == code or b["booking_id"] == code:
                return b
        return None