(function () {
  let activeHighlights = [];

  function injectStyles() {
    if (document.getElementById('clause-styles')) return;
    const style = document.createElement('style');
    style.id = 'clause-styles';
    style.textContent = `
      .clause-highlight {
        cursor: pointer;
        border-radius: 2px;
      }
      .clause-high {
        background: rgba(185, 28, 28, 0.15);
        border-bottom: 2px solid #b91c1c;
      }
      .clause-medium {
        background: rgba(180, 83, 9, 0.15);
        border-bottom: 2px solid #b45309;
      }
      .clause-low {
        background: rgba(21, 128, 61, 0.12);
        border-bottom: 2px solid #15803d;
      }
      #clause-tooltip {
        position: fixed;
        z-index: 2147483647;
        max-width: 320px;
        background: #0b1320;
        border: 1px solid #1e2d42;
        border-left: 3px solid var(--clause-tip-color, #b91c1c);
        border-radius: 3px;
        padding: 12px 14px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 13px;
        color: #e8e4d9;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
        pointer-events: none;
        line-height: 1.5;
      }
      #clause-tooltip .tip-badge {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 7px;
        opacity: 0.85;
      }
      #clause-tooltip .tip-explanation {
        margin-bottom: 0;
      }
      #clause-tooltip .tip-negotiate {
        margin-top: 9px;
        padding-top: 9px;
        border-top: 1px solid #1e2d42;
        font-size: 12px;
        color: #c4a35a;
        font-style: italic;
      }
      #clause-tooltip .tip-negotiate::before {
        content: 'Negotiate: ';
        font-weight: 600;
      }
    `;
    document.head.appendChild(style);
  }

  function setupTooltip() {
    let tooltip = document.getElementById('clause-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = 'clause-tooltip';
      tooltip.style.display = 'none';
      document.body.appendChild(tooltip);
    }

    document.addEventListener('mouseover', (e) => {
      const el = e.target.closest('.clause-highlight');
      if (!el) {
        tooltip.style.display = 'none';
        return;
      }
      try {
        const data = JSON.parse(el.dataset.clause || '{}');
        if (!data.explanation) return;

        const riskColor =
          data.risk_level === 'high' ? '#b91c1c' :
          data.risk_level === 'medium' ? '#b45309' : '#15803d';

        tooltip.style.setProperty('--clause-tip-color', riskColor);
        tooltip.innerHTML = `
          <div class="tip-badge" style="color:${riskColor}">
            ${(data.type || 'clause').replace(/_/g, ' ')} &mdash; ${(data.risk_level || '').toUpperCase()} RISK
          </div>
          <div class="tip-explanation">${data.explanation}</div>
          ${data.negotiation_tip ? `<div class="tip-negotiate">${data.negotiation_tip}</div>` : ''}
        `;
        tooltip.style.display = 'block';
      } catch (_) {
        tooltip.style.display = 'none';
      }
    });

    document.addEventListener('mousemove', (e) => {
      if (tooltip.style.display === 'none') return;
      const x = e.clientX + 14;
      const y = e.clientY + 14;
      tooltip.style.left = Math.min(x, window.innerWidth - 336) + 'px';
      tooltip.style.top = Math.min(y, window.innerHeight - 160) + 'px';
    });

    document.addEventListener('mouseout', (e) => {
      if (!e.target.closest('.clause-highlight')) return;
      if (!e.relatedTarget || !e.relatedTarget.closest('.clause-highlight')) {
        tooltip.style.display = 'none';
      }
    });
  }

  function highlightClause(clauseText, className, clauseData) {
    const snippet = clauseText.slice(0, 120).trim();
    if (snippet.length < 10) return;

    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const tag = node.parentElement && node.parentElement.tagName;
          if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(tag)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    let node;
    while ((node = walker.nextNode())) {
      const idx = node.textContent.indexOf(snippet);
      if (idx === -1) continue;

      try {
        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + snippet.length);

        const mark = document.createElement('mark');
        mark.className = `clause-highlight ${className}`;
        mark.style.background = 'none';
        mark.dataset.clause = JSON.stringify(clauseData);
        range.surroundContents(mark);
        activeHighlights.push(mark);
      } catch (_) {
        // surroundContents fails if the range spans multiple nodes; skip
      }
      break;
    }
  }

  function clearHighlights() {
    activeHighlights.forEach((el) => {
      if (!el.parentNode) return;
      const text = document.createTextNode(el.textContent);
      el.parentNode.replaceChild(text, el);
      text.parentNode && text.parentNode.normalize();
    });
    activeHighlights = [];
    const tooltip = document.getElementById('clause-tooltip');
    if (tooltip) tooltip.style.display = 'none';
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === 'EXTRACT_TEXT') {
      sendResponse({ text: document.body.innerText.slice(0, 50000) });
    } else if (msg.type === 'HIGHLIGHT_CLAUSES') {
      injectStyles();
      setupTooltip();
      clearHighlights();
      (msg.clauses || []).forEach((clause) => {
        const cls = `clause-${clause.risk_level || 'low'}`;
        highlightClause(clause.text, cls, clause);
      });
      sendResponse({ ok: true, count: activeHighlights.length });
    } else if (msg.type === 'CLEAR_HIGHLIGHTS') {
      clearHighlights();
      sendResponse({ ok: true });
    }
    return true;
  });
})();
