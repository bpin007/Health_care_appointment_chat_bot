export default function MessageBubble({ sender, text }) {
  const isUser = sender === "user";

  return (
    <div className={`flex w-full mb-2 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`
          px-4 py-2 max-w-[75%] rounded-xl text-sm leading-relaxed
          ${isUser
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-gray-100 text-gray-800 rounded-bl-none"
          }
        `}
      >
        {text}
      </div>
    </div>
  );
}
