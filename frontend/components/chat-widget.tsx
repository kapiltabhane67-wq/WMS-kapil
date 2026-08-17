"use client";
import { useState, useRef, useEffect } from "react";
import { API_BASE } from "../lib/constants";

interface Message {
  role: "user" | "assistant";
  content: string;
  error?: boolean;
}

interface ChatWidgetProps {
  token: string;
  role: string;
}

export function ChatWidget({ token, role }: ChatWidgetProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `👋 Hi! I'm your WMS AI Assistant. I have access to live warehouse data — inventory, orders, staff activity, receipts, and more.\n\nAsk me anything about operations! For example:\n• "How many pending orders are there?"\n• "Who is working on pick tasks?"\n• "What's the stock level for each product?"\n• "Show me recent activity"`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Only show for Admin and Manager. Keep this after hooks so changing roles
  // during the initial dashboard load does not violate React's hook ordering.
  if (!["ORG_ADMIN", "WAREHOUSE_MANAGER"].includes(role)) return null;

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          history: newMessages.slice(-10).map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `⚠️ ${data.detail || "Something went wrong."}`, error: true },
        ]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Unable to reach the AI service. Check your connection.", error: true },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function formatContent(text: string) {
    return text.split("\n").map((line, i) => (
      <span key={i}>
        {line}
        {i < text.split("\n").length - 1 && <br />}
      </span>
    ));
  }

  return (
    <>
      {/* Floating button */}
      <button
        className="chat-fab"
        onClick={() => setOpen((o) => !o)}
        title="AI Assistant"
        aria-label="Open AI chat assistant"
      >
        {open ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
        {!open && <span className="chat-fab-badge">AI</span>}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="chat-panel">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar">🤖</div>
              <div>
                <div className="chat-title">WMS AI Assistant</div>
                <div className="chat-subtitle">Live warehouse data · {role.replace("_", " ")}</div>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble-wrap ${msg.role}`}>
                {msg.role === "assistant" && <div className="chat-bot-icon">🤖</div>}
                <div className={`chat-bubble ${msg.role} ${msg.error ? "error" : ""}`}>
                  {formatContent(msg.content)}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble-wrap assistant">
                <div className="chat-bot-icon">🤖</div>
                <div className="chat-bubble assistant">
                  <span className="chat-typing">
                    <span /><span /><span />
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="chat-input-area">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about inventory, orders, staff..."
              rows={1}
              disabled={loading}
            />
            <button
              className="chat-send"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              title="Send (Enter)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <div className="chat-hint">Enter to send · Shift+Enter for new line</div>
        </div>
      )}
    </>
  );
}
