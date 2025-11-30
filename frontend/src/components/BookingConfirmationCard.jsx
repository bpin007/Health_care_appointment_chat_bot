export default function BookingConfirmationModal({ details, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center">
      <div className="bg-white p-6 rounded-2xl w-[360px] shadow-xl">

        <h2 className="text-lg font-semibold mb-4">
          🎉 Appointment Confirmed!
        </h2>

        <div className="space-y-1 text-gray-700 text-sm">
          <p>📅 {details.date}</p>
          <p>⏰ {details.start_time}</p>
          <p>🔖 Confirmation: {details.confirmation_code}</p>
        </div>

        <button
          onClick={onClose}
          className="bg-blue-600 text-white w-full py-2 mt-5 rounded-lg cursor-pointer"
        >
          Close
        </button>
      </div>
    </div>
  );
}
