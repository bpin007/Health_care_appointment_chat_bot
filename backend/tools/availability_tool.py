import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class AvailabilityTool:
    """
    Intelligent availability checker that generates time slots dynamically
    based on doctor schedules and existing bookings.
    """

    def __init__(self):
        # Load doctor profiles
        data_path = Path(__file__).resolve().parents[2] / "data" / "doctors.json"
        with open(data_path, "r") as f:
            self.doctors = json.load(f)
        
        # Load existing bookings (if file exists)
        bookings_path = Path(__file__).resolve().parents[2] / "data" / "bookings.json"
        try:
            with open(bookings_path, "r") as f:
                self.bookings = json.load(f)
        except FileNotFoundError:
            self.bookings = []  # No bookings yet

        # Map appointment types to specializations
        self.appointment_to_specialization = {
            "consultation": "General Physician",
            "followup": "General Physician",
            "follow-up": "General Physician",
            "physical": "General Physician",

            # Specialist types
            "dental": "Dentist",
            "pediatric": "Pediatrician",
            "cardio": "Cardiologist",
            "derma": "Dermatologist",
            "ortho": "Orthopedic Surgeon",

            # Generic specialist
            "specialist": None
        }

    def check(self, date: str, appointment_type: str, doctor_id: Optional[int] = None) -> List[Dict]:
        """
        Generate available time slots for a given date and appointment type.
        
        Args:
            date: Date in format "YYYY-MM-DD" or natural language like "tomorrow", "next Monday"
            appointment_type: Type of appointment (consultation, followup, physical, etc.)
            doctor_id: Optional specific doctor ID. If None, searches all relevant doctors.
        
        Returns:
            List of available time slots with doctor information
        """
        # Parse the date
        parsed_date = self._parse_date(date)
        if not parsed_date:
            return []
        
        day_of_week = parsed_date.strftime("%A")  # e.g., "Monday"
        date_str = parsed_date.strftime("%Y-%m-%d")
        
        # Find relevant doctors
        relevant_doctors = self._get_relevant_doctors(appointment_type, doctor_id, day_of_week)
        
        if not relevant_doctors:
            return []
        
        # Generate slots for each doctor
        all_slots = []
        for doctor in relevant_doctors:
            slots = self._generate_slots_for_doctor(doctor, date_str, day_of_week, appointment_type)
            all_slots.extend(slots)
        
        # Sort by time
        all_slots.sort(key=lambda x: x["start_time"])
        
        return all_slots

    def _parse_date(self, date: str) -> Optional[datetime]:
        """
        Parse various date formats including natural language.
        """
        date_lower = date.lower().strip()
        today = datetime.now().date()
        
        # Handle natural language dates
        if date_lower in ["today"]:
            return datetime.combine(today, datetime.min.time())
        
        if date_lower in ["tomorrow"]:
            return datetime.combine(today + timedelta(days=1), datetime.min.time())
        
        # Handle "next Monday", "this Friday", etc.
        days_of_week = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        for day_name, day_num in days_of_week.items():
            if day_name in date_lower:
                # Find next occurrence of this day
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return datetime.combine(target_date, datetime.min.time())
        
        # Try standard date formats
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%B %d", "%b %d"]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date, fmt)
                # If year not provided, assume current year
                if parsed.year == 1900:
                    parsed = parsed.replace(year=today.year)
                return parsed
            except ValueError:
                continue
        
        return None

    def _get_relevant_doctors(self, appointment_type: str, doctor_id: Optional[int], day_of_week: str) -> List[Dict]:
        """
        Find doctors who can handle this appointment type and work on this day.
        """
        if doctor_id:
            # Specific doctor requested
            doctor = next((d for d in self.doctors if d["doctor_id"] == doctor_id), None)
            if doctor and day_of_week in doctor["working_days"]:
                return [doctor]
            return []
        
        # Find doctors by specialization
        specialization = self.appointment_to_specialization.get(appointment_type, "General Physician")
        
        relevant = []
        for doctor in self.doctors:
            # Check if doctor works on this day
            if day_of_week not in doctor["working_days"]:
                continue
            
            # Check specialization match
            if specialization and doctor["specialization"] != specialization:
                continue
            
            relevant.append(doctor)
        
        return relevant

    def _generate_slots_for_doctor(self, doctor: Dict, date_str: str, day_of_week: str, appointment_type: str) -> List[Dict]:
        """
        Generate time slots for a specific doctor on a specific date.
        """
        slots = []
        
        # Get doctor's working hours
        start_time_str = doctor["working_hours"]["start"]
        end_time_str = doctor["working_hours"]["end"]
        slot_duration = doctor["appointment_duration_minutes"]
        
        # Parse times
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        # Generate slots
        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)
        
        while current_time + timedelta(minutes=slot_duration) <= end_datetime:
            slot_start = current_time.strftime("%H:%M")
            slot_end = (current_time + timedelta(minutes=slot_duration)).strftime("%H:%M")
            
            # Check if slot is booked
            is_available = self._is_slot_available(doctor["doctor_id"], date_str, slot_start)
            
            slots.append({
                "start_time": slot_start,
                "end_time": slot_end,
                "available": is_available,
                "duration": slot_duration,
                "doctor_id": doctor["doctor_id"],
                "doctor_name": doctor["name"],
                "specialization": doctor["specialization"]
            })
            
            current_time += timedelta(minutes=slot_duration)
        
        return slots

    def _is_slot_available(self, doctor_id: int, date: str, start_time: str) -> bool:
        """
        Check if a specific slot is available (not booked).
        """
        for booking in self.bookings:
            if (booking.get("doctor_id") == doctor_id and 
                booking.get("date") == date and 
                booking.get("start_time") == start_time):
                return False
        return True

    def get_doctor_by_id(self, doctor_id: int) -> Optional[Dict]:
        """Get doctor information by ID."""
        return next((d for d in self.doctors if d["doctor_id"] == doctor_id), None)

    def get_doctors_by_specialization(self, specialization: str) -> List[Dict]:
        """Get all doctors of a specific specialization."""
        return [d for d in self.doctors if d["specialization"] == specialization]

    def get_all_specializations(self) -> List[str]:
        """Get list of all available specializations."""
        return list(set(d["specialization"] for d in self.doctors))