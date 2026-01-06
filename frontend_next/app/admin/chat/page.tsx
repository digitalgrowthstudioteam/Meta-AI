"use client";

import { useEffect, useState } from "react";

type ChatThread = {
  thread_id: string;
  user_id: string;
  user_email: string;
  last_message: string | null;
  updated_at: string;
};

type ChatMessage = {
  id: string;
  sender: "user" | "admin";
  message: string;
  created_at: string;
};

export default function AdminChatPage() {
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThread, setActiveThread] = useState<ChatThread | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  // ---------------------------------------
  // LOAD ALL CHAT THREADS
  // ---------------------------------------
  useEffect(() => {
    const loadThreads = async () => {
      try {
        const res = await fetch("/api/admin/chat/threads", {
          credentials: "include",
        });
        const data = await res.json();
        setThreads(data || []);
      } finally {
        setLoadingThreads(false);
      }
    };

    loadThreads();
  }, []);

  // ---------------------------------------
  // LOAD MESSAGES FOR THREAD
  // ---------------------------------------
  const loadMessages = async (thread: ChatThread) => {
    setActiveThread(thread);
    setLoadingMessages(true);
    try {
      const res = await fetch(
        `/api/admin/chat/threads/${thread.thread_id}`,
        { credentials: "include" }
      );
      const data = await res.json();
      setMessages(data.messages || []);
    } finally {
      setLoadingMessages(false);
    }
  };

  // ---------------------------------------
  // SEND ADMIN MESSAGE
  // ---------------------------------------
  const sendMessage = async () => {
    if (!input.trim() || !activeThread) return;

    setSending(true);
    try {
      const res = await fetch("/api/admin/chat/message", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: activeThread.thread_id,
          message: input,
        }),
      });

      const data = await res.json();
      setMessages((prev) => [...prev, data]);
      setInput("");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-[75vh] bg-white border rounded-lg overflow-hidden">
      {/* LEFT — THREAD LIST */}
      <div className="w-72 border-r overflow-y-auto">
        <div className="px-4 py-3 border-b">
          <h2 className="text-sm font-medium text-gray-900">
            User Chats
          </h2>
          <p className="text-xs text-gray-500">
            All active conversations
          </p>
        </div>

        {loadingThreads ? (
          <div className="p-4 text-sm text-gray-500">Loading…</div>
        ) : threads.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">
            No chats yet.
          </div>
        ) : (
          threads.map((t) => (
            <button
              key={t.thread_id}
              onClick={() => loadMessages(t)}
              className={`w-full text-left px-4 py-3 border-b hover:bg-amber-50 ${
                activeThread?.thread_id === t.thread_id
                  ? "bg-amber-100"
                  : ""
              }`}
            >
              <div className="text-sm font-medium">
                {t.user_email}
              </div>
              <div className="text-xs text-gray-500 truncate">
                {t.last_message || "No messages yet"}
              </div>
            </button>
          ))
        )}
      </div>

      {/* RIGHT — CHAT WINDOW */}
      <div className="flex-1 flex flex-col">
        {!activeThread ? (
          <div className="flex-1 flex items-center justify-center text-sm text-gray-500">
            Select a conversation
          </div>
        ) : (
          <>
            {/* HEADER */}
            <div className="px-4 py-3 border-b">
              <div className="text-sm font-medium">
                {activeThread.user_email}
              </div>
              <div className="text-xs text-gray-500">
                User ID: {activeThread.user_id}
              </div>
            </div>

            {/* MESSAGES */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {loadingMessages ? (
                <div className="text-sm text-gray-500">
                  Loading messages…
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.sender === "admin"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                        msg.sender === "admin"
                          ? "bg-amber-600 text-white"
                          : "bg-gray-100 text-gray-900"
                      }`}
                    >
                      <div>{msg.message}</div>
                      <div className="mt-1 text-[10px] text-gray-400 text-right">
                        {new Date(
                          msg.created_at
                        ).toLocaleTimeString()}
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
                placeholder="Reply to user…"
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
          </>
        )}
      </div>
    </div>
  );
}
