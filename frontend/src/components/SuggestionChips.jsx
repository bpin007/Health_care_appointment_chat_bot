export default function SuggestionChips({ suggestions, onClick }) {
  if (!suggestions?.length) return null;

  return (
    <div className="flex flex-wrap gap-2 p-3">
      {suggestions.map((s, i) => (
        <button
          key={i}
          onClick={() => onClick(s)}
          className="
            px-3 py-1 rounded-full text-sm border
            bg-gray-100 hover:bg-gray-200 transition
          "
        >
          {s}
        </button>
      ))}
    </div>
  );
}
