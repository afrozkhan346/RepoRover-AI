"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"

interface ChatPanelProps {
  projectId: string
}

export default function ChatPanel({ projectId }: ChatPanelProps) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = { role: "user", content: input }
    setMessages([...messages, userMessage])
    setInput("")
    setLoading(true)

    try {
      const endpoint = process.env.NEXT_PUBLIC_CHAT_ENDPOINT

      if (endpoint) {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ projectId, message: input }),
        })

        if (response.ok) {
          const data = await response.json()
          setMessages((prev) => [...prev, { role: "assistant", content: data.response }])
        }
      } else {
        // Mock response
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "This is a helpful response about your question. In a real implementation, this would be powered by AI.",
          },
        ])
      }
    } catch (err) {
      console.error("Chat error:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="glass p-6 rounded-lg">
      <div className="h-64 overflow-y-auto mb-4 space-y-4">
        {messages.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">Ask questions about this project...</p>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-xs px-4 py-2 rounded-lg ${
                  msg.role === "user" ? "bg-purple-600 text-white" : "bg-white/10 text-foreground"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
          disabled={loading}
          className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
        />
        <Button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
        >
          Send
        </Button>
      </div>
    </div>
  )
}
