import json
import re
from typing import Dict, Any, List
from dateparser import parse
import httpx

from agent.llm import LLM
from agent.prompts import SYSTEM_PROMPT
from rag.faq_rag import FAQ_RAG
from tools.booking_tool import BookingTool


class SchedulingAgent:
    """
    Intelligent conversational agent for medical appointment scheduling.

    Flow: Reason → Type → Date → Time → Doctor → Slot → Name → Phone → Email → Confirm
    """

    APPOINTMENT_TYPES = {
        "consultation": {"duration": 30, "name": "General Consultation"},
        "followup": {"duration": 15, "name": "Follow-up"},
        "follow-up": {"duration": 15, "name": "Follow-up"},
        "physical": {"duration": 45, "name": "Physical Exam"},
        "specialist": {"duration": 60, "name": "Specialist Consultation"},
    }

    FAQ_PATTERNS = [
        r"\b(insurance|location|hours|parking|payment|policy|covid)\b",  # Removed "cancel"
        r"\b(what|how|where|when)\b.*\b(cost|price|bring|documents)\b",
    ]

    symptoms = [
        "pain",
        "hurt",
        "injury",
        "fever",
        "cough",
        "sick",
        "ache",
        "throat",
        "rash",
        "headache",
    ]

    illness_triggers = [
        "doctor",
        "clinic",
        "appointment",
        "book",
        "medical",
        "hospital",
        "checkup",
        "consult",
    ]

    def __init__(self):
        self.llm = LLM()
        self.rag = FAQ_RAG()
        self.booking_tool = BookingTool()
        self.session_memory = {}

    # =====================================================
    # MAIN CHAT HANDLER
    # =====================================================
    async def handle_message(
        self, user_message: str, session_id: str
    ) -> Dict[str, Any]:
        text = user_message.strip()
        text_l = text.lower()

        if session_id not in self.session_memory:
            self.session_memory[session_id] = self._new_session_state()

        memory = self.session_memory[session_id]

        # Check for cancellation intent FIRST (before FAQ)
        if "cancel" in text_l:
            # if user already has a booking in memory
            if memory.get("last_booking_id"):
                memory["state"] = "awaiting_cancel_confirm"
                return self._msg(
                    "⚠️ You already have an appointment.\n\n"
                    "Are you sure you want to cancel it? (yes/no)"
                )

            # otherwise ask for booking/confirmation code
            memory["state"] = "awaiting_cancellation_code"
            return self._msg(
                "Sure — please provide your confirmation code or booking id.\n"
                "Example:\n• APPT-1732829\n• ABC123"
            )

        # FAQ detection (after cancellation check)
        if self._is_faq(text_l):
            return self._handle_faq(memory, text)

        if memory["state"] == "awaiting_cancel_confirm":
            if "yes" in text_l:
                try:
                    result = self.booking_tool.cancel(memory["last_booking_id"])
                    memory["state"] = None
                    memory["last_booking_id"] = None
                    return self._msg(
                        "❌ Your appointment has been cancelled.\n\n"
                        "If you'd like to book again, I can help."
                    )
                except Exception as e:
                    return self._msg(f"❌ Could not cancel: {e}")

            # user said NO
            memory["state"] = None
            return self._msg("👍 Okay, I will keep your appointment.")

        # Handle cancellation code input
        if memory["state"] == "awaiting_cancellation_code":
            code = self._parse_confirmation_code(text)
            if not code:
                return self._msg(
                    "I couldn't detect a valid code.\n"
                    "Please provide something like:\n"
                    "• APPT-123456\n• ABC123"
                )

            booking = self.booking_tool.get_booking_by_confirmation(code)
            if not booking:
                return self._msg(
                    "❌ I couldn't find an active appointment with that code.\n"
                    "Please check your confirmation email."
                )

            # Save which booking user wants to cancel
            memory["cancel_target"] = booking
            memory["state"] = "awaiting_cancel_code_confirm"
            return self._msg(
                f"📋 Found your appointment:\n\n"
                f"📅 {booking.get('date')} at {booking.get('start_time')}\n"
                f"👨‍⚕️ {booking.get('doctor_name', 'Doctor')}\n\n"
                f"Are you sure you want to cancel? (yes/no)"
            )

        if memory["state"] == "awaiting_cancel_code_confirm":
            if "yes" in text_l:
                booking = memory["cancel_target"]
                result = self.booking_tool.cancel(booking["booking_id"])
                memory["cancel_target"] = None
                memory["last_booking_id"] = None
                memory["state"] = None

                return self._msg(
                    "❌ Appointment cancelled successfully.\n"
                    "If you'd like to rebook, just let me know!"
                )

            memory["state"] = None
            memory["cancel_target"] = None
            return self._msg("👍 Ok, I will keep your appointment.")

        # Reset conversation
        if "restart" in text_l or "start over" in text_l:
            self.session_memory[session_id] = self._new_session_state()
            return self._msg("Got it, let's start fresh. What brings you in today?")

        # First interaction
        if memory["state"] is None:
            return await self._initial(text, text_l, memory)

        # 1️⃣ Capture Reason
        if memory["state"] == "awaiting_reason":
            # Validate: Check if user provided actual information
            if not self._is_valid_reason(text):
                return self._msg(
                    "I'd like to help! Could you tell me what brings you in?\n\n"
                    "For example:\n"
                    "• 'I have a headache'\n"
                    "• 'I need a checkup'\n"
                    "• 'Follow-up appointment'"
                )
            
            memory["reason"] = text
            memory["state"] = "awaiting_appointment_type"
            return self._suggest_appt_type(text)

        # 2️⃣ Appointment type
        if memory["state"] == "awaiting_appointment_type":
            # Allow "yes" to accept suggested type
            if any(
                word in text_l
                for word in ["yes", "y", "ok", "okay", "sure", "sounds good", "fine", "perfect"]
            ):
                apt_type = "consultation"  # Default suggested type
            else:
                apt_type = self._parse_appt_type(text_l)

            if not apt_type:
                return self._ask_appt_type()

            memory["appointment_type"] = apt_type
            memory["state"] = "awaiting_date"

            info = self.APPOINTMENT_TYPES[apt_type]
            return self._msg(
                f"Great! I'll schedule a **{info['name']}** ({info['duration']}m).\n\n"
                f"When would you like to come in?\n"
                f"Try:\n• tomorrow\n• next Monday\n• March 5\n• in 2 days"
            )

        # 3️⃣ Date
        if memory["state"] == "awaiting_date":
            normalized = self._parse_date(text)
            if not normalized:
                return self._msg(
                    "I didn't understand that date. Please try:\n"
                    "• tomorrow\n"
                    "• next Monday\n"
                    "• December 15\n"
                    "• in 3 days"
                )

            memory["preferred_date"] = normalized
            memory["state"] = "awaiting_time"
            return self._msg("Got it! Morning ☀️ Afternoon 🌤️ or Evening 🌙 ?")

        # 4️⃣ Time preference → Doctor list
        if memory["state"] == "awaiting_time":
            time_pref = self._parse_time(text_l)
            if not time_pref:
                return self._msg(
                    "Please choose a time of day:\n"
                    "• Morning ☀️\n"
                    "• Afternoon 🌤️\n"
                    "• Evening 🌙"
                )

            memory["preferred_time_of_day"] = time_pref

            doctors = await self._fetch_doctors(memory)
            if not doctors:
                return self._msg(
                    "No doctors available for that time. Try a different time or date."
                )

            memory["doctors"] = doctors
            memory["state"] = "awaiting_doctor"
            return {
                "action": "doctors",
                "message": "Here are available doctors 👇",
                "doctors": doctors,
            }

        # 5️⃣ Doctor selection → Fetch slots
        if memory["state"] == "awaiting_doctor":
            selected = self._pick_doctor(text, memory["doctors"])
            if not selected:
                return self._msg(
                    "Please select a doctor by saying:\n"
                    "• first\n"
                    "• second\n"
                    "• 1 or 2\n"
                    "• Dr. Smith"
                )

            memory["doctor"] = selected

            slots = await self._fetch_slots(memory)
            if not slots:
                return self._msg(
                    "No slots available with this doctor. Try another date."
                )

            memory["available_slots"] = slots
            memory["state"] = "awaiting_slot"
            return {
                "action": "slots",
                "message": f"📅 Available times with **{selected['name']}**:",
                "slots": slots[:8],
            }

        # 6️⃣ Slot selection
        if memory["state"] == "awaiting_slot":
            choice = self._pick_slot(text, memory["available_slots"])
            if not choice:
                return self._msg(
                    "Please select a time slot:\n"
                    "• 10:30\n"
                    "• first or earliest\n"
                    "• 1, 2, 3..."
                )

            memory["selected_slot"] = choice
            memory["state"] = "awaiting_name"
            return self._msg("Perfect 👍 What's your full name?")

        # 7️⃣ Name
        if memory["state"] == "awaiting_name":
            if len(text.split()) < 2:
                return self._msg(
                    "Please provide your full name (first and last name).\n"
                    "Example: John Smith"
                )
            memory["patient"]["name"] = text
            memory["state"] = "awaiting_phone"
            return self._msg("Great! What's your phone number?")

        # 8️⃣ Phone
        if memory["state"] == "awaiting_phone":
            if not self._valid_phone(text):
                return self._msg(
                    "That doesn't look like a valid phone number.\n"
                    "Please provide a 10-digit phone number.\n"
                    "Example: 555-123-4567"
                )
            memory["patient"]["phone"] = text
            memory["state"] = "awaiting_email"
            return self._msg("And your email address?")

        # 9️⃣ Email
        if memory["state"] == "awaiting_email":
            if not self._valid_email(text):
                return self._msg(
                    "That email looks invalid. Please try again.\n"
                    "Example: john@example.com"
                )
            memory["patient"]["email"] = text
            memory["state"] = "awaiting_confirm"
            return self._msg(self._summary(memory) + "\n\n✅ Confirm? (yes/no)")

        # 🔟 Confirm booking
        if memory["state"] == "awaiting_confirm":
            if "yes" in text_l or "confirm" in text_l or "book" in text_l:
                try:
                    result = self._book(memory)
                    memory["state"] = "completed"
                    memory["last_booking_id"] = result[
                        "booking_id"
                    ]  # Store for potential cancellation
                    return {
                        "action": "booking_confirmed",
                        "details": result,
                        "message": (
                            f"🎉 **Appointment confirmed!**\n\n"
                            f"📅 {memory['preferred_date']} at {memory['selected_slot']}\n"
                            f"👨‍⚕️ {memory['doctor']['name']}\n"
                            f"🔖 Confirmation: **{result['confirmation_code']}**\n\n"
                            f"See you then! 👋"
                        ),
                    }
                except Exception as e:
                    return self._msg(f"❌ Booking failed: {str(e)}\nPlease try again.")

            # User wants to change something
            return self._msg(
                "No problem! What would you like to change?\n(date, time, doctor, or cancel)"
            )

        # Fallback to LLM
        try:
            llm_out = await self.llm.respond(SYSTEM_PROMPT, user_message)
            parsed = json.loads(llm_out)
            return {
                "action": "reply",
                "message": parsed.get("message", "I didn't understand that."),
            }
        except:
            return self._msg("Sorry, I didn't understand that 🙏\nCould you rephrase?")

    # =====================================================
    # SESSION STATE
    # =====================================================
    def _new_session_state(self):
        return {
            "state": None,
            "reason": None,
            "appointment_type": None,
            "preferred_date": None,
            "preferred_time_of_day": None,
            "doctor": None,
            "selected_slot": None,
            "patient": {},
            "doctors": [],
            "available_slots": [],
            "last_booking_id": None,
            "cancel_target": None,
        }

    # =====================================================
    # INITIAL MESSAGE HANDLING
    # =====================================================
    async def _initial(self, text: str, text_l: str, memory: Dict) -> Dict[str, Any]:
        """Handle the first user message"""

        # Greeting detection - don't advance state yet
        greetings = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        
        # Check if message is ONLY a greeting (no additional info)
        is_pure_greeting = any(text_l.strip() == g or text_l.strip() == g + "!" for g in greetings)
        
        if is_pure_greeting:
            memory["state"] = "awaiting_reason"
            return self._msg(
                "Hello 👋! I'm here to help you schedule an appointment.\n\n"
                "What brings you in today?"
            )

        # Symptom detection - auto-store as reason
        symptoms = [
            "pain",
            "hurt",
            "injury",
            "fever",
            "cough",
            "sick",
            "ache",
            "throat",
            "rash",
            "headache",
        ]
        if any(s in text_l for s in symptoms):
            memory["reason"] = text
            memory["state"] = "awaiting_appointment_type"
            return self._msg(
                "Thanks for sharing 🙏\n\n"
                "Based on your symptoms, I'd recommend a **General Consultation (30 min)**.\n"
                "Does that work for you?"
            )

        # Booking intent keywords
        booking_words = [
            "appointment",
            "book",
            "schedule",
            "visit",
            "see doctor",
            "consultation",
        ]
        if any(w in text_l for w in booking_words):
            memory["state"] = "awaiting_reason"
            return self._msg("Sure! What's the reason for your appointment?")

        # Default - ask for reason
        memory["state"] = "awaiting_reason"
        return self._msg(
            "I'm here to help you book an appointment 😊\n\n"
            "What brings you in today?"
        )

    # =====================================================
    # VALIDATION HELPERS
    # =====================================================
    def _is_valid_reason(self, text: str) -> bool:
        """Check if user provided a valid reason (not just greeting/filler)"""
        text_l = text.lower().strip()
        
        # Filter out pure greetings
        greetings = ["hi", "hello", "hey", "yo", "sup"]
        if text_l in greetings:
            return False
        
        # Must be at least 3 characters and contain meaningful content
        if len(text) < 3:
            return False
        
        # Check for meaningful words
        meaningful_patterns = [
            r'\b(pain|hurt|sick|fever|cough|checkup|consultation|followup|exam)\b',
            r'\b(need|want|schedule|book|appointment)\b',
        ]
        
        return any(re.search(pattern, text_l) for pattern in meaningful_patterns) or len(text.split()) >= 3

    # =====================================================
    # FAQ HANDLING
    # =====================================================
    def _handle_faq(self, memory: Dict, question: str) -> Dict[str, Any]:
        """Handle FAQ questions using RAG"""
        answer = self.rag.query(question)

        # If user is mid-booking, guide them back
        if memory["state"] and memory["state"] not in ["completed", None]:
            return self._msg(answer + "\n\n" + self._get_return_prompt(memory))

        # Otherwise, offer to book
        return self._msg(answer + "\n\nWould you like to schedule an appointment?")

    def _get_return_prompt(self, memory: Dict) -> str:
        """Get contextual prompt to continue booking"""
        prompts = {
            "awaiting_reason": "Now, what brings you in?",
            "awaiting_appointment_type": "What type of appointment would you like?",
            "awaiting_date": "When would you like to come in?",
            "awaiting_time": "What time of day works best?",
            "awaiting_doctor": "Which doctor would you prefer?",
            "awaiting_slot": "Which time slot works for you?",
            "awaiting_name": "What's your full name?",
            "awaiting_phone": "What's your phone number?",
            "awaiting_email": "What's your email address?",
            "awaiting_confirm": "Should I confirm this booking?",
        }
        return prompts.get(memory["state"], "Let's continue with your booking.")

    # =====================================================
    # APPOINTMENT TYPE HELPERS
    # =====================================================
    def _suggest_appt_type(self, reason: str) -> Dict[str, Any]:
        """Suggest appointment type based on reason"""
        r = reason.lower()

        # Check for urgency indicators
        urgent = ["urgent", "severe", "emergency", "bad", "terrible", "can't", "unable"]
        if any(word in r for word in urgent):
            return self._msg(
                "That sounds urgent 😟\n\n"
                "I recommend a **General Consultation (30 min)**.\n"
                "Does that work?"
            )

        # Default suggestion
        return self._msg(
            "Thanks for sharing 🙏\n\n"
            "I'd recommend a **General Consultation (30 min)**.\n"
            "Is that okay?"
        )

    # =====================================================
    # API CALLS
    # =====================================================
    async def _fetch_doctors(self, mem):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://localhost:8000/api/calendly/doctors",
                    params={
                        "date": mem["preferred_date"],
                        "appointment_type": mem["appointment_type"],
                    },
                    timeout=10,
                )
            resp.raise_for_status()
            return resp.json().get("doctors", [])

        except Exception as e:
            print(f"❌ Error fetching doctors: {e}")
            return []

    async def _fetch_slots(self, mem):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://localhost:8000/api/calendly/availability",
                    params={
                        "date": mem["preferred_date"],
                        "appointment_type": mem["appointment_type"],
                        "doctor_id": mem["doctor"]["doctor_id"],
                    },
                    timeout=10,
                )
            resp.raise_for_status()
            return resp.json().get("available_slots", [])

        except Exception as e:
            print(f"❌ Error fetching slots: {e}")
            return []

    # =====================================================
    # BOOKING
    # =====================================================
    def _book(self, mem):
        payload = {
            "doctor_id": mem["doctor"]["doctor_id"],
            "appointment_type": mem["appointment_type"],
            "date": mem["preferred_date"],
            "start_time": mem["selected_slot"],
            "patient_name": mem["patient"]["name"],
            "patient_email": mem["patient"]["email"],
            "patient_phone": mem["patient"]["phone"],
            "reason": mem["reason"],
        }
        return self.booking_tool.book(payload)

    # =====================================================
    # PARSING HELPERS
    # =====================================================
    def _msg(self, text: str) -> Dict[str, Any]:
        """Helper to create reply action"""
        return {"action": "reply", "message": text}

    def _is_faq(self, text: str) -> bool:
        """Check if message is an FAQ question"""
        return any(re.search(pattern, text) for pattern in self.FAQ_PATTERNS)

    def _parse_confirmation_code(self, text: str) -> str:
        """Extract confirmation code from user input"""
        # Look for pattern like APPT-123456
        match = re.search(r"APPT-\d+", text.upper())
        if match:
            return match.group()

        # Look for 6-character alphanumeric code
        match = re.search(r"\b([A-Z0-9]{6})\b", text.upper())
        if match:
            return match.group()

        return None

    def _parse_appt_type(self, text: str) -> str:
        """Extract appointment type from user input"""
        for key in self.APPOINTMENT_TYPES:
            if key in text:
                return key

        # Fuzzy matching
        if "consult" in text:
            return "consultation"
        if "exam" in text or "physical" in text or "checkup" in text:
            return "physical"
        if "specialist" in text:
            return "specialist"

        return None

    def _ask_appt_type(self) -> Dict[str, Any]:
        """Ask user to select appointment type"""
        return self._msg(
            "Which type of appointment?\n\n"
            "• General Consultation (30 min)\n"
            "• Follow-Up (15 min)\n"
            "• Physical Exam (45 min)\n"
            "• Specialist Consultation (60 min)"
        )

    def _parse_time(self, text: str) -> str:
        """Extract time preference from user input"""
        if "morning" in text or "am" in text:
            return "morning"
        if "afternoon" in text or "noon" in text or "pm" in text:
            return "afternoon"
        if "evening" in text or "night" in text:
            return "evening"
        return None

    def _parse_date(self, user_input: str) -> str:
        """Parse natural language date to YYYY-MM-DD"""
        parsed = parse(user_input)
        return parsed.strftime("%Y-%m-%d") if parsed else None

    def _pick_doctor(self, text: str, doctors: List[Dict]) -> Dict:
        """Select doctor from list based on user input"""
        t = text.lower()

        # Ordinal words
        ordinals = {"first": 0, "second": 1, "third": 2, "1st": 0, "2nd": 1, "3rd": 2}
        for word, idx in ordinals.items():
            if word in t and idx < len(doctors):
                return doctors[idx]

        # Number matching
        match = re.search(r"\b([1-9])\b", t)
        if match:
            idx = int(match.group()) - 1
            if 0 <= idx < len(doctors):
                return doctors[idx]

        # Name matching
        for doctor in doctors:
            if doctor["name"].lower() in t:
                return doctor

        return None

    def _pick_slot(self, text: str, slots: List[Dict]) -> str:
        """Select slot from list based on user input"""
        t = text.lower()

        # Special keywords
        if "earliest" in t or "first available" in t:
            return slots[0]["start_time"]
        if "latest" in t or "last" in t:
            return slots[-1]["start_time"]

        # Exact time match
        for slot in slots:
            if slot["start_time"] in text:
                return slot["start_time"]

        # Number selection (1, 2, 3...)
        match = re.search(r"\b([1-9])\b", t)
        if match:
            idx = int(match.group()) - 1
            if 0 <= idx < len(slots):
                return slots[idx]["start_time"]

        return None

    def _valid_phone(self, phone: str) -> bool:
        """Validate phone number"""
        digits = re.sub(r"\D", "", phone)
        return len(digits) >= 10

    def _valid_email(self, email: str) -> bool:
        """Validate email address"""
        return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))

    def _summary(self, mem: Dict) -> str:
        """Create booking summary"""
        doctor = mem["doctor"]
        appt = self.APPOINTMENT_TYPES[mem["appointment_type"]]

        return (
            f"📋 **Booking Summary:**\n\n"
            f"🩺 {appt['name']} ({appt['duration']} min)\n"
            f"👨‍⚕️ {doctor['name']} - {doctor.get('specialization', 'General Physician')}\n"
            f"📅 {mem['preferred_date']}\n"
            f"⏰ {mem['selected_slot']}\n"
            f"👤 {mem['patient']['name']}\n"
            f"📞 {mem['patient']['phone']}\n"
            f"📧 {mem['patient']['email']}\n"
            f"💭 Reason: {mem['reason']}"
        )