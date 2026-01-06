"use client";

import { useEffect, useState } from "react";

type ChatMessage = {
  id: string;
  sender: "user" | "admin";
  message: string;
  created_at: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  // ---------------------------------------
  // LOAD CHAT HISTORY
  // ---------------------------------------
  useEffect(() => {
    const loadChat = async () => {
      try {
        const res = await fetch("/api/chat/thread", {
          credentials: "include",
        });
        const data = await res.json();
        setMessages(data.messages || []);
      } finally {
        setLoading(false);
      }
    };

    loadChat();
  }, []);

  // ---------------------------------------
  // SEND MESSAGE
  // ---------------------------------------
  const sendMessage = async () => {
    if (!input.trim()) return;

    setSending(true);
    try {
      const res = await fetch("/api/chat/message", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();
      setMessages((prev) => [...prev, data]);
      setInput("");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white border rounded-lg flex flex-col h-[70vh]">
      {/* HEADER */}
      <div className="px-4 py-3 border-b">
        <h2 className="text-sm font-medium text-gray-900">
          Support Chat
        </h2>
        <p className="text-xs text-gray-500">
          Chat with Digital Growth Studio support
        </p>
      </div>

      {/* MESSAGES */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="text-sm text-gray-500">Loading chat…</div>
        ) : messages.length === 0 ? (
          <div className="text-sm text-gray-500">
            No messages yet. Say hello 👋
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                  msg.sender === "user"
                    ? "bg-amber-100 text-amber-900"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                <div>{msg.message}</div>
                <div className="mt-1 text-[10px] text-gray-400 text-right">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* INPUT */}
      <div className="border-t p-3 flex gap-2">
        <input
          type="text"
          className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-300"
          placeholder="Type your message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendMessage();
          }}
        />
        <button
          onClick={sendMessage}
          disabled={sending}
          className="px-4 py-2 rounded-md text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
