import DoctorCard from "./DoctorCard";

export default function DoctorList({ doctors, onSelect }) {
  if (!doctors || doctors.length === 0)
    return <p className="text-slate-500 text-sm">No doctors available.</p>;

  return (
    <div className="flex flex-col gap-3 mt-4">
      {doctors.map((doc) => (
        <DoctorCard key={doc.id} doctor={doc} onSelect={onSelect} />
      ))}
    </div>
  );
}
