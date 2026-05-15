const analyzeBtn = document.getElementById('analyzeBtn');
const freelancerToggle = document.getElementById('freelancerMode');
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const resultsEl = document.getElementById('results');
const riskValue = document.getElementById('riskValue');
const riskBanner = document.getElementById('riskBanner');
const summaryEl = document.getElementById('summary');
const clauseList = document.getElementById('clauseList');
const freelancerSection = document.getElementById('freelancerSection');
const freelancerList = document.getElementById('freelancerList');
const clearBtn = document.getElementById('clearBtn');

function setLoading(on) {
  analyzeBtn.disabled = on;
  loadingEl.classList.toggle('hidden', !on);
}

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
}

function clearError() {
  errorEl.classList.add('hidden');
  errorEl.textContent = '';
}

function renderRisk(level) {
  riskValue.textContent = level.toUpperCase();
  riskValue.className = `risk-value ${level}`;
}

function renderClause(clause, index) {
  const card = document.createElement('div');
  card.className = `clause-card ${clause.risk_level || 'low'}`;

  const typeLabel = (clause.type || 'clause').replace(/_/g, ' ');

  card.innerHTML = `
    <div class="clause-header">
      <div class="clause-meta">
        <span class="clause-dot"></span>
        <span class="clause-type">${typeLabel}</span>
      </div>
      <span class="chevron">&#9660;</span>
    </div>
    <div class="clause-body">
      <div class="clause-explanation">${clause.explanation || ''}</div>
      ${clause.negotiation_tip ? `<div class="clause-tip">${clause.negotiation_tip}</div>` : ''}
    </div>
  `;

  card.querySelector('.clause-header').addEventListener('click', () => {
    card.classList.toggle('open');
  });

  return card;
}

analyzeBtn.addEventListener('click', async () => {
  clearError();
  resultsEl.classList.add('hidden');
  setLoading(true);

  chrome.runtime.sendMessage(
    { type: 'ANALYZE', freelancer_mode: freelancerToggle.checked },
    (response) => {
      setLoading(false);

      if (chrome.runtime.lastError) {
        showError(chrome.runtime.lastError.message);
        return;
      }

      if (!response || response.error) {
        showError(response ? response.error : 'No response from background.');
        return;
      }

      const { analysis, isPdf } = response;

      renderRisk(analysis.overall_risk || 'low');
      summaryEl.textContent = analysis.summary || '';

      clauseList.innerHTML = '';
      const clauses = analysis.clauses || [];
      if (clauses.length === 0) {
        const none = document.createElement('p');
        none.style.cssText = 'font-size:12px;color:#555570;text-align:center;padding:8px 0';
        none.textContent = 'No high-risk clauses detected.';
        clauseList.appendChild(none);
      } else {
        clauses.forEach((c, i) => clauseList.appendChild(renderClause(c, i)));
      }

      freelancerList.innerHTML = '';
      const flags = analysis.freelancer_flags || [];
      if (freelancerToggle.checked && flags.length > 0) {
        flags.forEach((f) => {
          const li = document.createElement('li');
          li.textContent = f.issue || '';
          freelancerList.appendChild(li);
        });
        freelancerSection.classList.remove('hidden');
      } else {
        freelancerSection.classList.add('hidden');
      }

      clearBtn.style.display = isPdf ? 'none' : '';
      resultsEl.classList.remove('hidden');
    }
  );
});

clearBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    chrome.tabs.sendMessage(tab.id, { type: 'CLEAR_HIGHLIGHTS' });
  });
  resultsEl.classList.add('hidden');
  clearError();
});
