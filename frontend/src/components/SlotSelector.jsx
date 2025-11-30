export default function SlotSelector({ slots, onSelect }) {
  if (!slots?.length) return null;

  return (
    <div className="mt-4 flex flex-col gap-3">
      {slots.map((slot, i) => (
        <button
          key={i}
          onClick={() => onSelect(slot.start_time)}
          className="
            flex justify-between items-center w-full
            px-4 py-3 border rounded-xl bg-white hover:bg-blue-50 transition
          "
        >
          <div>
            <p className="font-medium text-gray-900">{slot.start_time}</p>
            <p className="text-xs text-gray-500">{slot.doctor_name}</p>
          </div>

          <span className="text-sm text-blue-600 font-semibold">
            Select
          </span>
        </button>
      ))}
    </div>
  );
}
