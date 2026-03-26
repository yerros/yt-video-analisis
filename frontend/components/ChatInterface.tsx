"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import type { ChatSession, ChatMessage } from "@/lib/types";
import { MarkdownMessage } from "./MarkdownMessage";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  referencedJobs?: string[];
  createdAt?: Date;
}

export function ChatInterface() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [input]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoadingSessions(true);
      const sessionList = await api.chat.listSessions();
      setSessions(sessionList);
      
      // Auto-select the most recent session if available
      if (sessionList.length > 0 && !currentSession) {
        await selectSession(sessionList[0].id);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    } finally {
      setLoadingSessions(false);
    }
  };

  const selectSession = async (sessionId: string) => {
    try {
      const session = await api.chat.getSession(sessionId);
      setCurrentSession(session);
      
      // Convert ChatMessage[] to Message[]
      const loadedMessages: Message[] = (session.messages || []).map((msg: ChatMessage) => ({
        id: msg.id,
        role: msg.role as "user" | "assistant",
        content: msg.content,
        referencedJobs: msg.referenced_jobs,
        createdAt: new Date(msg.created_at),
      }));
      
      setMessages(loadedMessages);
    } catch (error) {
      console.error("Failed to load session:", error);
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await api.chat.createSession();
      setSessions([newSession, ...sessions]);
      setCurrentSession(newSession);
      setMessages([]);
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm("Are you sure you want to delete this chat?")) {
      return;
    }

    try {
      await api.chat.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
      
      // If deleting current session, clear messages
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/chat/message/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: userMessage.content,
          session_id: currentSession?.id,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server responded with error:", response.status, errorText);
        throw new Error(`Failed to send message: ${response.status} - ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      const assistantMessage: Message = {
        id: Date.now().toString() + "_assistant",
        role: "assistant",
        content: "",
        createdAt: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              try {
                const parsed = JSON.parse(data);

                if (parsed.session_id && !currentSession) {
                  // New session was created, reload sessions list
                  await loadSessions();
                  const newSession = await api.chat.getSession(parsed.session_id);
                  setCurrentSession(newSession);
                }

                if (parsed.content) {
                  assistantMessage.content += parsed.content;
                  setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = { ...assistantMessage };
                    return updated;
                  });
                }

                if (parsed.done) {
                  if (parsed.referenced_jobs) {
                    assistantMessage.referencedJobs = parsed.referenced_jobs;
                  }
                  // Reload sessions to update message count
                  loadSessions();
                  break;
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString() + "_error",
          role: "assistant",
          content: "I apologize, but I encountered an error processing your request. Please try again.",
          createdAt: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatSessionTitle = (session: ChatSession) => {
    if (session.title) return session.title;
    const date = new Date(session.created_at);
    return `${date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })} - ${date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}`;
  };

  const formatTime = (date?: Date) => {
    if (!date) return "";
    return date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
  };

  const copyMessageToClipboard = async (messageId: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error("Failed to copy message:", error);
    }
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* Sidebar - Session History */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-white">
          <button
            onClick={createNewSession}
            className="w-full px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all font-medium flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Conversation
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          {loadingSessions ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-8 h-8 border-3 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <p className="text-sm text-gray-600 font-medium">No conversations yet</p>
              <p className="text-xs text-gray-500 mt-1">Start chatting to see your history</p>
            </div>
          ) : (
            <div className="p-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => selectSession(session.id)}
                  className={`group relative px-3 py-3 rounded-xl cursor-pointer transition-all mb-1 ${
                    currentSession?.id === session.id
                      ? "bg-indigo-50 border-2 border-indigo-200 shadow-sm"
                      : "hover:bg-gray-50 border-2 border-transparent"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className={`w-2 h-2 rounded-full ${
                          currentSession?.id === session.id ? "bg-indigo-600" : "bg-gray-300"
                        }`} />
                        <p className={`text-sm font-semibold truncate ${
                          currentSession?.id === session.id ? "text-indigo-900" : "text-gray-900"
                        }`}>
                          {formatSessionTitle(session)}
                        </p>
                      </div>
                      <p className="text-xs text-gray-500 ml-4">
                        {session.message_count || 0} messages
                      </p>
                    </div>
                    <button
                      onClick={(e) => deleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 rounded-lg transition-all"
                      title="Delete conversation"
                    >
                      <svg className="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-md">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">AI Video Assistant</h2>
                <p className="text-sm text-gray-500">Powered by GPT-4o</p>
              </div>
            </div>
            {currentSession && (
              <div className="text-right">
                <p className="text-xs text-gray-500">Session ID</p>
                <p className="text-xs font-mono text-gray-400">{currentSession.id.slice(0, 8)}...</p>
              </div>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-100 to-indigo-50 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
                  <svg
                    className="w-10 h-10 text-indigo-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Ask me anything about your videos
                </h3>
                <p className="text-gray-600 max-w-md leading-relaxed">
                  I can help you analyze, summarize, compare, and find insights from all your analyzed YouTube videos.
                </p>
                <div className="mt-6 grid grid-cols-2 gap-3 max-w-2xl">
                  <div className="bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-indigo-300 transition-colors">
                    <p className="text-sm font-medium text-gray-900 mb-1">📊 Summarize</p>
                    <p className="text-xs text-gray-600">Get quick summaries of video content</p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-indigo-300 transition-colors">
                    <p className="text-sm font-medium text-gray-900 mb-1">🔍 Search</p>
                    <p className="text-xs text-gray-600">Find specific topics or themes</p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-indigo-300 transition-colors">
                    <p className="text-sm font-medium text-gray-900 mb-1">📈 Compare</p>
                    <p className="text-xs text-gray-600">Compare multiple videos side by side</p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-indigo-300 transition-colors">
                    <p className="text-sm font-medium text-gray-900 mb-1">💡 Insights</p>
                    <p className="text-xs text-gray-600">Extract key insights and trends</p>
                  </div>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"} group`}
              >
                {message.role === "assistant" && (
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                  </div>
                )}

                <div className={`flex flex-col ${message.role === "user" ? "items-end" : "items-start"} max-w-[75%]`}>
                  <div className="relative">
                    <div
                      className={`rounded-2xl px-5 py-3 shadow-sm ${
                        message.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-white border border-gray-200 text-gray-900"
                      }`}
                    >
                      {/* Copy button for assistant messages */}
                      {message.role === "assistant" && (
                        <button
                          onClick={() => copyMessageToClipboard(message.id, message.content)}
                          className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 p-1.5 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-all"
                          title="Copy message"
                        >
                          {copiedMessageId === message.id ? (
                            <svg className="w-3.5 h-3.5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <svg className="w-3.5 h-3.5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          )}
                        </button>
                      )}

                      {/* Use MarkdownMessage for assistant, keep simple formatting for user */}
                      {message.role === "assistant" ? (
                        <MarkdownMessage 
                          content={message.content}
                          className="text-gray-900"
                        />
                      ) : (
                        <div className="text-[15px] leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </div>
                      )}
                      
                      {message.referencedJobs && message.referencedJobs.length > 0 && (
                        <div className={`mt-3 pt-3 ${message.role === "user" ? "border-t border-indigo-500" : "border-t border-gray-200"}`}>
                          <div className="flex items-center gap-2">
                            <svg className={`w-4 h-4 ${message.role === "user" ? "text-indigo-200" : "text-gray-500"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <p className={`text-xs font-medium ${message.role === "user" ? "text-indigo-200" : "text-gray-600"}`}>
                              Referenced {message.referencedJobs.length} video{message.referencedJobs.length > 1 ? 's' : ''}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-xs text-gray-500 mt-1.5 px-2">
                    {formatTime(message.createdAt)}
                  </p>
                </div>

                {message.role === "user" && (
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-gradient-to-br from-gray-600 to-gray-700 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-4 justify-start">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-md">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-5 py-4 shadow-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white px-6 py-4 shadow-lg">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message..."
                  className="w-full resize-none border-2 border-gray-200 rounded-2xl px-5 py-3.5 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-[15px] leading-relaxed max-h-32 overflow-y-auto"
                  rows={1}
                  disabled={isLoading}
                  style={{ minHeight: "52px" }}
                />
                <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                  {input.length > 0 && `${input.length} chars`}
                </div>
              </div>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="px-6 py-3.5 bg-indigo-600 text-white rounded-2xl hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all font-medium shadow-md hover:shadow-lg flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    <span>Send</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">Enter</kbd> to send · <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">Shift + Enter</kbd> for new line
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
