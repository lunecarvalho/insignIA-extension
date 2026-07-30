"use strict";
(() => {
  // src/services/api.ts
  var BACKEND_URL = "http://127.0.0.1:8000/api/analisar";
  async function sendConversation(conversation) {
    const res = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(conversation)
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API error: ${res.status} - ${text}`);
    }
    const body = await res.json();
    return body;
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
