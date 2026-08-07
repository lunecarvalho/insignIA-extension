"use strict";
(() => {
  // src/services/api.ts
  var BACKEND_URL = "http://127.0.0.1:8000/analyze";
  async function sendConversation(conversation) {
    const payload = {
      chat_id: conversation.id ?? crypto.randomUUID(),
      canal: "chrome-extension",
      mensagens: conversation.messages.map((m) => m.text).filter(Boolean)
    };
    const res = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API error: ${res.status} - ${text}`);
    }
    const body = await res.json();
    return {
      reason: body.reason,
      sentiment: body.sentiment,
      quality: body.quality,
      trends: body.trends ?? {},
      insights: Array.isArray(body.insights_list) ? body.insights_list : body.insights ? [String(body.insights)] : []
    };
  }

  // src/background.ts
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === "analyze") {
      handleAnalyze(message.conversation, sender);
      return true;
    }
  });
  async function handleAnalyze(conversation, sender) {
    try {
      const result = await sendConversation(conversation);
      const tabId = sender?.tab?.id;
      if (typeof tabId === "number") {
        chrome.tabs.sendMessage(tabId, { type: "analysisResult", payload: result });
      }
    } catch (err) {
      console.error("InsignIA background: erro ao analisar conversa", err);
      const tabId = sender?.tab?.id;
      if (typeof tabId === "number") {
        chrome.tabs.sendMessage(tabId, { type: "analysisResult", payload: { error: String(err) } });
      }
    }
  }
})();
