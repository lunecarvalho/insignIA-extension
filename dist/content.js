"use strict";
(() => {
  // src/utils/serializer.ts
  function normalizeConversation(raw, sourceUrl) {
    const conv = {
      id: raw?.id ?? `conv_${Date.now()}`,
      url: sourceUrl ?? raw?.url ?? window.location.href,
      messages: []
    };
    const items = Array.isArray(raw) ? raw : raw?.messages ?? [];
    for (const m of items) {
      const msg = {
        role: m?.role ?? m?.author ?? (m?.from ? String(m.from) : "unknown"),
        text: String(m?.text ?? m?.content ?? m?.message ?? "").trim(),
        timestamp: m?.timestamp ?? m?.time ?? void 0
      };
      if (msg.text)
        conv.messages.push(msg);
    }
    return conv;
  }

  // src/content.ts
  function injectAnalyzeButton() {
    if (document.getElementById("insignia-analyze-btn"))
      return;
    const btn = document.createElement("button");
    btn.id = "insignia-analyze-btn";
    btn.innerText = "\u{1F50D} Analisar Conversa";
    Object.assign(btn.style, {
      position: "fixed",
      right: "18px",
      bottom: "24px",
      zIndex: "999999",
      padding: "12px 14px",
      borderRadius: "12px",
      background: "linear-gradient(135deg,#5b5ceb,#00d2c7)",
      color: "white",
      border: "none",
      boxShadow: "0 10px 30px rgba(16,24,40,0.12)",
      fontWeight: "700"
    });
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      btn.innerText = "\u23F3 Extraindo...";
      try {
        const conv = extractConversation();
        chrome.runtime.sendMessage({ type: "analyze", conversation: conv }, (resp) => {
        });
      } catch (err) {
        console.error("InsignIA: erro ao extrair conversa", err);
      } finally {
        btn.disabled = false;
        btn.innerText = "\u{1F50D} Analisar Conversa";
      }
    });
    document.body.appendChild(btn);
  }
  function extractConversation() {
    const selectors = [
      "[data-message]",
      ".message",
      ".chat-message",
      ".msg",
      ".bubble",
      "li.message",
      ".convo-item"
    ];
    let nodes = [];
    for (const s of selectors) {
      const found = Array.from(document.querySelectorAll(s));
      if (found.length > 0) {
        nodes = found;
        break;
      }
    }
    if (nodes.length === 0) {
      const containers = Array.from(document.querySelectorAll('[role="log"], [aria-live]'));
      if (containers.length) {
        nodes = Array.from(containers[0].querySelectorAll("p,div,li"));
      }
    }
    const raw = nodes.map((el) => {
      const author = (el.querySelector(".author") || el.querySelector(".from") || el.getAttribute("data-author"))?.textContent?.trim();
      const text = (el.querySelector(".text") || el.querySelector(".content") || el).textContent?.trim() ?? "";
      const ts = el.getAttribute("data-time") || el.querySelector("time")?.getAttribute("datetime") || void 0;
      return { role: author ?? void 0, text, timestamp: ts };
    });
    return normalizeConversation(raw, window.location.href);
  }
  function ensurePanel() {
    let panel = document.getElementById("insignia-panel");
    if (panel)
      return panel;
    panel = document.createElement("aside");
    panel.id = "insignia-panel";
    panel.setAttribute("aria-hidden", "false");
    Object.assign(panel.style, {
      position: "fixed",
      right: "18px",
      top: "18px",
      width: "360px",
      height: "84vh",
      background: "white",
      borderRadius: "16px",
      boxShadow: "0 24px 70px rgba(16,24,40,0.08)",
      border: "1px solid rgba(229,233,242,0.9)",
      zIndex: "999999",
      overflow: "auto",
      padding: "14px",
      display: "flex",
      flexDirection: "column",
      gap: "10px"
    });
    const header = document.createElement("div");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";
    const title = document.createElement("strong");
    title.innerText = "InsignIA \u2014 Resultados";
    title.style.fontSize = "14px";
    const close = document.createElement("button");
    close.innerText = "\u2715";
    Object.assign(close.style, { background: "transparent", border: "none", cursor: "pointer" });
    close.addEventListener("click", () => panel?.remove());
    header.appendChild(title);
    header.appendChild(close);
    panel.appendChild(header);
    const body = document.createElement("div");
    body.id = "insignia-panel-body";
    body.style.display = "flex";
    body.style.flexDirection = "column";
    body.style.gap = "10px";
    panel.appendChild(body);
    document.body.appendChild(panel);
    return panel;
  }
  function renderAnalysis(result) {
    const panel = ensurePanel();
    const body = panel.querySelector("#insignia-panel-body");
    body.innerHTML = "";
    if (!result || result.error || !("reason" in result)) {
      const errorCard = document.createElement("div");
      errorCard.style.padding = "12px";
      errorCard.style.borderRadius = "12px";
      errorCard.style.border = "1px solid #ffe0e0";
      errorCard.innerHTML = `<h4 style="margin:0 0 6px 0">Falha na an\xE1lise</h4>
    <div style="color:#b42318">N\xE3o foi poss\xEDvel conectar \xE0 API. Verifique se o backend FastAPI est\xE1 rodando em http://127.0.0.1:8000.</div>`;
      body.appendChild(errorCard);
      return;
    }
    const resultData = result;
    const reasonCard = document.createElement("div");
    reasonCard.style.padding = "10px";
    reasonCard.style.borderRadius = "12px";
    reasonCard.style.border = "1px solid var(--border, #eef2ff)";
    reasonCard.innerHTML = `<h4 style="margin:0 0 6px 0">Motivo do Atendimento</h4>
  <div style="font-weight:700">${resultData.reason.category}</div>
  <div style="color:#697386;font-size:12px">${resultData.reason.subcategory}</div>
  <div style="margin-top:8px;font-weight:800">Confian\xE7a: ${resultData.reason.confidence}%</div>`;
    body.appendChild(reasonCard);
    const sentCard = document.createElement("div");
    sentCard.style.padding = "10px";
    sentCard.style.borderRadius = "12px";
    sentCard.style.border = "1px solid var(--border, #eef2ff)";
    sentCard.innerHTML = `<h4 style="margin:0 0 6px 0">An\xE1lise de Sentimento</h4>
  <div style="font-weight:700">${resultData.sentiment.label} (${resultData.sentiment.score})</div>`;
    body.appendChild(sentCard);
    const qCard = document.createElement("div");
    qCard.style.padding = "10px";
    qCard.style.borderRadius = "12px";
    qCard.style.border = "1px solid var(--border, #eef2ff)";
    const checklistHtml = Object.entries(resultData.quality.checklist).map(([k, v]) => `<div>${v ? "\u2714" : "\u2716"} ${k}</div>`).join("");
    qCard.innerHTML = `<h4 style="margin:0 0 6px 0">Qualidade do Atendimento</h4>
  <div style="font-weight:800">${resultData.quality.score}/100</div>
  <div style="margin-top:8px">${checklistHtml}</div>
  <div style="margin-top:8px;color:#697386">${resultData.quality.notes ?? ""}</div>`;
    body.appendChild(qCard);
    const iCard = document.createElement("div");
    iCard.style.padding = "10px";
    iCard.style.borderRadius = "12px";
    iCard.style.border = "1px solid var(--border, #eef2ff)";
    iCard.innerHTML = `<h4 style="margin:0 0 6px 0">Insights da IA</h4>
  <ul style="margin:0;padding-left:18px">${resultData.insights.map((i) => `<li>${i}</li>`).join("")}</ul>`;
    body.appendChild(iCard);
  }
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === "analysisResult") {
      try {
        renderAnalysis(message.payload);
      } catch (err) {
        console.error("InsignIA: erro ao renderizar an\xE1lise", err);
      }
    }
    return true;
  });
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === "startFromPopup") {
      try {
        const conv = extractConversation();
        chrome.runtime.sendMessage({ type: "analyze", conversation: conv });
        sendResponse({ status: "ok" });
      } catch (err) {
        sendResponse({ status: "error", message: String(err) });
      }
    }
    return true;
  });
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectAnalyzeButton);
  } else {
    injectAnalyzeButton();
  }
})();
