import { useState, useRef, useEffect } from "react";
import { askCortexAgent } from "../lib/snowflake";

/**
 * Floating chat panel for interacting with the Cortex Agent.
 * Streams responses from the Cortex REST API in real time.
 */

interface Message {
  role: "user" | "agent";
  text: string;
}

export default function Chat({ accountContext }: { accountContext?: string }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);

    // Prepend account context so the agent knows which account the user is looking at
    const agentQuery = accountContext
      ? `I am currently looking at the account "${accountContext}". Answer my question specifically about this account. Use all available data sources.\n\nQuestion: ${text}`
      : text;

    // Add a placeholder agent message that we'll update as chunks arrive
    const agentMsgIndex = messages.length + 1; // +1 for user message just added

    try {
      const reply = await askCortexAgent(agentQuery, (textSoFar) => {
        // Update the streaming agent message in place
        setMessages((prev) => {
          const updated = [...prev];
          // If we already have the agent message, update it
          if (updated.length > agentMsgIndex) {
            updated[agentMsgIndex] = { role: "agent", text: textSoFar };
          } else {
            // Add the agent message for the first chunk
            updated.push({ role: "agent", text: textSoFar });
          }
          return updated;
        });
      });

      // Final update with complete text
      setMessages((prev) => {
        const updated = [...prev];
        if (updated.length > agentMsgIndex) {
          updated[agentMsgIndex] = { role: "agent", text: reply };
        } else {
          updated.push({ role: "agent", text: reply });
        }
        return updated;
      });
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Unknown error calling Cortex Agent";
      setMessages((prev) => [
        ...prev.filter((_, i) => i < agentMsgIndex), // remove partial streaming msg if any
        {
          role: "agent",
          text: `Error: ${errorMsg}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 z-40 rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-500 flex items-center gap-2 px-5 py-3 transition-colors"
        aria-label="Toggle chat"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443h.166c3.868 0 7.221-1.674 7.221-4.72 0-3.048-3.353-4.72-7.221-4.72-3.867 0-7.22 1.672-7.22 4.72Z" />
        </svg>
        <span className="text-sm font-medium">Ask the Agent</span>
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-20 right-6 z-40 w-96 rounded-xl border border-gray-800 bg-gray-900 shadow-2xl flex flex-col overflow-hidden"
          style={{ height: "28rem" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-200">
              Cortex Agent{accountContext ? <span className="text-indigo-400 font-normal ml-1">· {accountContext}</span> : null}
            </h3>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-500 hover:text-gray-300 text-xs"
            >
              Close
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <p className="text-sm text-gray-500 italic">
                {accountContext
                  ? `Ask about ${accountContext} — the agent has full context on this account.`
                  : "Ask about account health, usage trends, or churn risk..."}
              </p>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-indigo-600/20 text-indigo-200 ml-8"
                    : "bg-gray-800 text-gray-300 mr-8"
                }`}
              >
                {msg.text}
              </div>
            ))}
            {loading && messages[messages.length - 1]?.role !== "agent" && (
              <div className="bg-gray-800 text-gray-500 rounded-lg px-3 py-2 text-sm mr-8 animate-pulse">
                Thinking...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="border-t border-gray-800 p-3 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about an account..."
              className="flex-1 rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
