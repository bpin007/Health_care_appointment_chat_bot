import { useMutation } from "@tanstack/react-query";
import axios from "axios";

export function useChat(sessionId) {
  return useMutation({
    mutationFn: async (message) => {
      const res = await axios.post("http://localhost:8000/api/chat", {
        message,
        session_id: sessionId,
      });

      return res.data.response;
    },
  });
}
