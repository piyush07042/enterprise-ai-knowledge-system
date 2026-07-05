import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./ChatPage.css";

export default function ChatPage() {
  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingId, setStreamingId] = useState(null);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);
  const streamTimerRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchChats();

    return () => {
      if (streamTimerRef.current) {
        clearInterval(streamTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const authHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });

  const fetchChats = async () => {
    try {
      const res = await api.get("/chats", {
        headers: authHeaders(),
      });

      const chatList = Array.isArray(res.data) ? res.data : [];
      setChats(chatList);

      if (chatList.length > 0) {
        await openChat(chatList[0].id);
      } else {
        await createChat();
      }
    } catch (err) {
      setError("Unable to load chats");
    }
  };

  const openChat = async (chatId) => {
    try {
      setError("");
      const res = await api.get(`/chats/${chatId}`, {
        headers: authHeaders(),
      });

      setActiveChat(res.data);
      setMessages(res.data.messages || []);
    } catch (err) {
      setError("Unable to open chat");
    }
  };

  const createChat = async () => {
    try {
      setError("");
      const res = await api.post(
        "/chats",
        { title: "New Chat" },
        {
          headers: authHeaders(),
        }
      );

      setActiveChat(res.data);
      setMessages([]);
      setChats((current) => [res.data, ...current]);
    } catch (err) {
      setError("Unable to create chat");
    }
  };

  const deleteChat = async () => {
    if (!activeChat) {
      return;
    }

    try {
      setError("");
      await api.delete(`/chats/${activeChat.id}`, {
        headers: authHeaders(),
      });

      const remaining = chats.filter((chat) => chat.id !== activeChat.id);
      setChats(remaining);

      if (remaining.length > 0) {
        await openChat(remaining[0].id);
      } else {
        setActiveChat(null);
        setMessages([]);
        await createChat();
      }
    } catch (err) {
      setError("Unable to delete chat");
    }
  };

  const streamAssistantMessage = (message) => {
    let index = 0;
    const fullText = message.content || "";

    setStreamingId(message.id);
    setMessages((current) => [
      ...current,
      {
        ...message,
        content: "",
      },
    ]);

    if (streamTimerRef.current) {
      clearInterval(streamTimerRef.current);
    }

    streamTimerRef.current = setInterval(() => {
      index += 3;
      setMessages((current) =>
        current.map((item) =>
          item.id === message.id
            ? { ...item, content: fullText.slice(0, index) }
            : item
        )
      );

      if (index >= fullText.length) {
        clearInterval(streamTimerRef.current);
        streamTimerRef.current = null;
        setStreamingId(null);
      }
    }, 18);
  };

  const sendMessage = async (event) => {
    event.preventDefault();

    const text = input.trim();
    if (!text || loading || !activeChat) {
      return;
    }

    setInput("");
    setLoading(true);
    setError("");

    const optimisticMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: text,
    };

    setMessages((current) => [...current, optimisticMessage]);

    try {
      const res = await api.post(
        `/chats/${activeChat.id}/messages`,
        { message: text },
        {
          headers: authHeaders(),
        }
      );

      setMessages((current) =>
        current.map((message) =>
          message.id === optimisticMessage.id ? res.data.user_message : message
        )
      );

      setActiveChat((current) => ({
        ...current,
        ...res.data.chat,
      }));

      setChats((current) => {
        const updatedChat = res.data.chat;
        const withoutUpdated = current.filter((chat) => chat.id !== updatedChat.id);
        return [updatedChat, ...withoutUpdated];
      });

      streamAssistantMessage(res.data.assistant_message);
    } catch (err) {
      setMessages((current) =>
        current.filter((message) => message.id !== optimisticMessage.id)
      );
      setError("Message failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page">
      <aside className="chat-sidebar">
        <div className="chat-sidebar-header">
          <button className="chat-back" onClick={() => navigate("/dashboard")}>
            Back
          </button>
          <button className="chat-new" onClick={createChat}>
            New Chat
          </button>
        </div>

        <div className="chat-list">
          {chats.map((chat) => (
            <button
              key={chat.id}
              className={`chat-list-item ${activeChat?.id === chat.id ? "active" : ""}`}
              onClick={() => openChat(chat.id)}
            >
              <span>{chat.title || "New Chat"}</span>
              <small>{chat.message_count || 0} messages</small>
            </button>
          ))}
        </div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <div>
            <p className="chat-kicker">Enterprise AI</p>
            <h1>{activeChat?.title || "New Chat"}</h1>
          </div>

          <button className="chat-delete" onClick={deleteChat}>
            Delete Chat
          </button>
        </header>

        {error && <div className="chat-error">{error}</div>}

        <section className="chat-window">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <h2>Ask your knowledge base</h2>
              <p>Start a conversation and I will answer from your uploaded documents.</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`chat-message-row ${message.role === "user" ? "user" : "assistant"}`}
              >
                <div className="chat-bubble">
                  <p>{message.content}</p>
                  {streamingId === message.id && <span className="typing-cursor" />}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </section>

        <form className="chat-composer" onSubmit={sendMessage}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Message Enterprise AI..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? "Thinking" : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}
