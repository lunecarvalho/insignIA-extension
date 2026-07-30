"use strict";
(() => {
  // src/popup.ts
  var analyzeBtn = document.getElementById("popup-analyze-btn");
  var statusNode = document.getElementById("popup-status");
  var summaryNode = document.getElementById("popup-summary");
  function setStatus(text) {
    if (statusNode)
      statusNode.innerText = text;
  }
  async function triggerAnalysisFromPopup() {
    setStatus("Enviando solicita\xE7\xE3o ao conte\xFAdo...");
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab || !tab.id) {
        setStatus("Nenhuma aba ativa encontrada");
        return;
      }
      chrome.tabs.sendMessage(tab.id, { type: "startFromPopup" }, (response) => {
        if (chrome.runtime.lastError) {
          setStatus("Erro: conte\xFAdo n\xE3o responde nesta p\xE1gina");
          console.warn("InsignIA popup: sendMessage error", chrome.runtime.lastError.message);
          return;
        }
        setStatus("An\xE1lise em andamento \u2014 aguarde...");
      });
    });
  }
  if (analyzeBtn) {
    analyzeBtn.addEventListener("click", (e) => {
      analyzeBtn.disabled = true;
      triggerAnalysisFromPopup();
      setTimeout(() => analyzeBtn.disabled = false, 2e3);
    });
  }
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === "analysisResult") {
      const payload = message.payload;
      if (payload?.reason) {
        if (summaryNode) {
          summaryNode.innerHTML = `<strong>${payload.reason.category}</strong> \u2014 ${payload.reason.subcategory} <div style="color:#697386;font-size:12px">Confian\xE7a ${payload.reason.confidence}%</div>`;
        }
        setStatus("An\xE1lise conclu\xEDda");
      } else if (payload?.error) {
        setStatus("Erro na an\xE1lise: " + payload.error);
      }
    }
    return true;
  });
  setStatus("Pronto");
})();
