export default function DoctorCard({ doctor, onSelect }) {
  return (
    <div
      onClick={() => onSelect(doctor)}
      className="
        flex items-center gap-4 p-4
        rounded-xl shadow-md bg-white hover:bg-slate-50
        border border-slate-200 cursor-pointer transition
      "
    >
      {/* Avatar */}
      <img
        src={doctor.image}
        alt={doctor.name}
        className="w-14 h-14 rounded-full object-cover"
      />

      <div className="flex flex-col flex-1">
        <div className="font-semibold text-slate-800 text-lg">
          {doctor.name}
        </div>

        <div className="text-sm text-slate-500">
          {doctor.specialization}
        </div>

        <div className="text-xs text-slate-400 mt-1">
          ⭐ {doctor.rating} / 5.0
        </div>
      </div>

      <button
        className="
          px-3 py-1 bg-blue-600 text-white rounded-md
          text-sm hover:bg-blue-700 transition
        "
      >
        Select
      </button>
    </div>
  );
}
