"use client";

import { ChatInterface } from "@/components/ChatInterface";
import { Header } from "@/components/Header";

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      {/* Chat Container */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
          <ChatInterface />
        </div>
      </div>
    </div>
  );
}
