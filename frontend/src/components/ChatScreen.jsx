import { useState, useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import SlotSelector from "./SlotSelector";
import SuggestionChips from "./SuggestionChips";
import ChatInput from "./ChatInput";
import { useChat } from "../hooks/useChat";
import BookingConfirmationModal from "./BookingConfirmationCard";
import DoctorList from "./DoctorList";

export default function ChatScreen() {
    // Persistent session ID
    const [session] = useState(() => {
        let id = localStorage.getItem("session_id");
        if (!id) {
            id = crypto.randomUUID();
            localStorage.setItem("session_id", id);
        }
        console.log("📋 Session ID:", id);
        return id;
    });

    const { mutateAsync } = useChat(session);

    const [messages, setMessages] = useState([]);
    const [slots, setSlots] = useState([]);
    const [bookingDetails, setBookingDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [initialized, setInitialized] = useState(false);
    const [doctors, setDoctors] = useState([])

    const scrollRef = useRef(null);

    // Restore persistent chat on mount
    useEffect(() => {
        console.log("🔄 Restoring chat from localStorage...");

        const m = localStorage.getItem("chat_messages");
        const s = localStorage.getItem("chat_slots");
        const b = localStorage.getItem("chat_booking");

        if (m) {
            const parsed = JSON.parse(m);
            console.log("✅ Restored messages:", parsed.length);
            setMessages(parsed);
        } else {
            console.log("ℹ️ No messages in localStorage");
            // Add initial greeting if no messages
            setMessages([
                {
                    sender: "agent",
                    text: "Hello 👋! I can help you schedule an appointment.\n\nWhat brings you in today?"
                }
            ]);
        }

        if (s) {
            const parsed = JSON.parse(s);
            console.log("✅ Restored slots:", parsed.length);
            setSlots(parsed);
        }

        if (b) {
            console.log("✅ Restored booking details");
            setBookingDetails(JSON.parse(b));
        }

        setInitialized(true);
    }, []);

    // Persist messages
    useEffect(() => {
        if (!initialized) return; // Don't save during initial load

        console.log("💾 Saving messages to localStorage:", messages.length);
        localStorage.setItem("chat_messages", JSON.stringify(messages));

        // Auto-scroll to bottom
        setTimeout(() => {
            scrollRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }, [messages, initialized]);

    // Persist slots
    useEffect(() => {
        if (!initialized) return;

        console.log("💾 Saving slots to localStorage:", slots.length);
        localStorage.setItem("chat_slots", JSON.stringify(slots));
    }, [slots, initialized]);

    // Persist booking
    useEffect(() => {
        if (!initialized) return;

        if (bookingDetails) {
            console.log("💾 Saving booking details to localStorage");
            localStorage.setItem("chat_booking", JSON.stringify(bookingDetails));
        }
    }, [bookingDetails, initialized]);

    async function sendUserMessage(text) {
        if (!text.trim()) return;

        console.log("📤 Sending message:", text);

        // Add user message
        setMessages((p) => [...p, { sender: "user", text }]);

        // Clear slots when user sends new message
        setSlots([]);
        localStorage.removeItem("chat_slots");

        setLoading(true);

        try {
            console.log("🔄 Calling API...");
            const res = await mutateAsync(text);
            console.log("✅ API Response:", res);

            if (res.action === "reply") {
                setMessages((p) => [...p, { sender: "agent", text: res.message }]);
            }

            if (res.action === "slots") {
                setMessages((p) => [...p, { sender: "agent", text: res.message }]);
                setSlots(res.slots);
            }

            if (res.action === "booking_confirmed") {
                setMessages((p) => [...p, { sender: "agent", text: res.message }]);
                setBookingDetails(res.details);
            }
            if (res.action === "doctors") {
                setMessages(prev => [...prev, { sender: "agent", text: res.message }]);
                setDoctors(res.doctors);
            }

        } catch (error) {
            console.error("❌ Error:", error);
            setMessages((p) => [
                ...p,
                {
                    sender: "agent",
                    text: "Sorry, something went wrong. Please try again."
                }
            ]);
        } finally {
            setLoading(false);
        }
    }

    // Clear chat function
    function clearChat() {
        console.log("🗑️ Clearing chat...");
        localStorage.removeItem("chat_messages");
        localStorage.removeItem("chat_slots");
        localStorage.removeItem("chat_booking");
        localStorage.removeItem("session_id");
        window.location.reload();
    }

    return (
        <div className="flex flex-col h-screen max-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-blue-600 text-white p-4 font-semibold text-lg shadow flex justify-between items-center">
                <span>🏥 HealthCare Assistant</span>
                <button
                    onClick={clearChat}
                    className="text-sm bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded"
                >
                    🔄 Reset Chat
                </button>
            </div>

            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 && (
                    <div className="text-gray-400 text-center mt-10">
                        No messages yet. Say hello! 👋
                    </div>
                )}

                {messages.map((m, i) => (
                    <MessageBubble key={i} {...m} />
                ))}

                {slots.length > 0 && (
                    <SlotSelector slots={slots} onSelect={sendUserMessage} />
                )}
                {doctors.length > 0 && (
                    <DoctorList
                        doctors={doctors}
                        onSelect={(d) => {
                            sendUserMessage(d.name);
                            setDoctors([]); 
                        }}
                    />
                )}
                


                {loading && (
                    <div className="flex gap-1 items-center text-gray-400 text-sm animate-pulse">
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    </div>
                )}

                <div ref={scrollRef}></div>
            </div>

            {/* Suggestions */}
            <SuggestionChips onClick={sendUserMessage} />

            {/* Input */}
            <ChatInput onSend={sendUserMessage} />

            {bookingDetails && (
                <BookingConfirmationModal
                    details={bookingDetails}
                    onClose={() => {
                        setBookingDetails(null);
                        localStorage.removeItem("chat_booking");
                    }}
                />
            )}
        </div>
    );
}