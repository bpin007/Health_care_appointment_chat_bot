# 🏥 AI Healthcare Appointment Assistant

An intelligent **LLM-powered medical appointment scheduling system** that replicates real clinic workflows — not a simple Q/A bot.

The assistant helps users understand symptoms, choose appointment types, find doctors, generate available slots, and confirm bookings.  
Think **ZocDoc / Apple Health appointment booking** done conversationally.

---

## 🌟 Key Features

### 🤖 AI Scheduling Agent
Conversational & human-like workflow:

**Reason → Type → Date → Time → Doctor → Slot → Contact → Confirm**

The agent:
- Extracts intent
- Suggests appointment types
- Validates answers
- Handles missing info
- Books or cancels appointments

---

### 🔁 Persistent UX
Your chat context remains intact even after browser refresh.  
Persisted fields:
- `session_id`
- `messages`
- `slots`
- `booking details`

No conversation resets.

---

### 👨‍⚕️ Doctor Intelligence
Smart filtering engine:
- by **specialization**
- by **working days**
- by **time of day**
- excludes **fully booked days**

---

### 🗓️ Dynamic Slot Generator
Backend-generated time slots based on:
- Doctor working hours
- Appointment duration
- Already booked slots

---

### ❌ Cancellation Flow
Users can cancel by:
- Saying phrases like:  
  > "cancel my appointment"
- Confirmation code
- Booking ID

---

### 💬 Human-like UI
Frontend includes:
- Chat bubbles
- Suggestion chips
- Doctor cards
- Time slot buttons
- Confirmation modal

---

## 🏗️ Project Architecture

```bash
root
├── backend
│   ├── agent
│   │   ├── scheduling_agent.py
│   │   ├── llm.py
│   │   └── prompts.py
│   ├── tools
│   │   ├── booking_tool.py
│   │   └── availability_tool.py
│   ├── models
│   │   └── schemas.py
│   └── data
│       ├── doctors.json
│       └── bookings.json
│
└── frontend
    ├── components
    ├── hooks
    ├── pages
    └── utils
```

---

## 🧠 Agent Flow (State Machine)

The agent never hallucinates — it follows strict states:

- `awaiting_reason`
- `awaiting_appointment_type`
- `awaiting_date`
- `awaiting_time`
- `awaiting_doctor`
- `awaiting_slot`
- `awaiting_name`
- `awaiting_phone`
- `awaiting_email`
- `awaiting_confirm`
- `completed`

Each step validates & moves forward logically.

---

## ⚙️ Tech Stack

### 🖥️ Backend
- FastAPI
- Custom LLM wrapper
- httpx
- dateparser
- JSON-based storage

### 🎨 Frontend
- React + Vite
- Tailwind CSS
- Custom chat components

---

# 🚀 Getting Started

## 1️⃣ Clone Repository
```bash
git clone <repo_url>
cd <project_folder>
```

---

## 2️⃣ Backend Setup

Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

Run API server:
```bash
uvicorn main:app --reload
```

📡 API runs at:  
👉 http://localhost:8000

---

## 3️⃣ Frontend Setup

Install dependencies:
```bash
cd frontend
npm install
```

Run app:
```bash
npm run dev
```

🌐 App runs at:  
👉 http://localhost:5173

---

# 🧠 Backend APIs

### 🔹 Get Doctors (filtered)
**GET** `/api/calendly/doctors?date=2025-12-02&appointment_type=consultation`

**Response:**
```json
{
  "doctors": [
    {
      "doctor_id": 1,
      "name": "Dr. Ashik Arya",
      "specialization": "General Physician",
      "rating": 4.7
    }
  ]
}
```

---

### 🔹 Get Time Slots
**GET** `/api/calendly/availability?date=2025-12-02&appointment_type=consultation&doctor_id=1`

**Response:**
```json
{
  "date": "2025-12-02",
  "available_slots": [
    {"start_time": "09:00", "end_time": "09:30", "doctor_id": 1, "available": true}
  ]
}
```

---

### 🔹 Book Appointment
**POST** `/api/calendly/book`

**Payload**
```json
{
  "doctor_id": 1,
  "date": "2025-12-02",
  "start_time": "09:00",
  "appointment_type": "consultation",
  "patient_name": "Bipin",
  "patient_email": "example@gmail.com",
  "patient_phone": "9876543210",
  "reason": "fever"
}
```

**Response**
```json
{
  "booking_id": "APPT-173248281",
  "confirmation_code": "CDF321",
  "status": "confirmed"
}
```

---

### 🔹 Cancel Appointment
Internal agent call:
```python
agent → booking_tool.cancel("APPT-12345678")
```

**Response**
```json
{
  "booking_id": "APPT-1234",
  "status": "cancelled",
  "message": "Appointment cancelled successfully."
}
```

---

# 💬 Chatbot UX

Key UI components:
- `MessageBubble`
- `SuggestionChips`
- `DoctorList`
- `SlotSelector`
- `BookingConfirmationModal`

### Frontend Logic Example
```ts
if (res.action === "slots") setSlots(res.slots);
if (res.action === "doctors") setDoctors(res.doctors);
if (res.action === "booking_confirmed") setBookingDetails(res.details);
```

---

# 💾 Local Persistence

Stored in browser:
- `messages`
- `booking details`
- `slots`
- `session_id`

⏳ Even after refresh → conversation continues.

---

# 🛠️ RAG + FAQ

User may ask about:
- Clinic hours
- Insurance
- Documents
- Parking
- Cancellation
- Policies

RAG provides **consistent + grounded answers**.

---

# 🔥 Cancellation Example

User:  
> I want to cancel

Agent:  
> Please provide your confirmation code.

User:  
> APPT-123456

Agent:  
> Found your booking on Dec 2, 09:00. Would you like to cancel?

User:  
> yes

Agent:  
> Appointment cancelled successfully.

---

# 🧪 API Testing (Postman)

1. Start backend  
2. Test:

```bash
/api/calendly/doctors
/api/calendly/availability
/api/calendly/book
```

Make sure payloads match the examples above.

---

# 🗂️ Data Files

### 📄 doctors.json
- Doctor profiles  
- Work days  
- Time windows  
- Appointment duration  

### 📄 bookings.json
- Stores bookings  
- Simulates mini-clinic database  

---

# ✨ Future Enhancements

- OAuth patient profiles
- Google Calendar / Outlook sync
- Real DB (Postgres / MongoDB)
- Payment integration
- Twilio reminders
- Multi-language support

---

# 🤝 Contributing

Pull requests are welcome!
- Fork
- Create branch
- Submit PR
- Or report issues

---

# 📄 License

MIT License

---

# ⭐ Feedback

If this project helps you — star ⭐ the repo  
and feel free to reach out 🙌

---

### End Note

This project demonstrates how AI should **assist**, not just respond.  
**Architecture > Prompt magic.**
