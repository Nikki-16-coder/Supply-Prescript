/**
 * SupplyPrescript - Dashboard Application Controller
 * Closed-Loop Prescriptive Analytics for Microchip Supply Chain Decision Support
 */

const API_BASE = window.location.origin.startsWith('http') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

let currentPrescription = null;

// ============================================================================
// Initialization & Health Check
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initHealthCheck();
  initTabNavigation();
  initPresetButtons();
  initFormHandlers();
  loadMlMetrics();
});

async function initHealthCheck() {
  const badge = document.getElementById('backendStatusBadge');
  const text = document.getElementById('backendStatusText');
  try {
    const res = await fetch(`${API_BASE}/`);
    if (res.ok) {
      badge.style.background = 'rgba(16, 185, 129, 0.15)';
      badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      badge.style.color = '#10b981';
      text.textContent = 'Backend Live (FastAPI)';
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    badge.style.background = 'rgba(244, 63, 94, 0.15)';
    badge.style.borderColor = 'rgba(244, 63, 94, 0.3)';
    badge.style.color = '#f43f5e';
    text.textContent = 'Backend Offline';
  }
}

// ============================================================================
// Tab Navigation
// ============================================================================
function initTabNavigation() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.remove('hidden');
      }

      if (targetId === 'tab-audit') {
        loadAuditTrail();
      }
    });
  });

  const refreshBtn = document.getElementById('btnRefreshAudit');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', loadAuditTrail);
  }
}

// ============================================================================
// Quick Scenario Presets
// ============================================================================
function initPresetButtons() {
  const presets = {
    presetStandard: {
      id: 'CHIP-TSMC-8840',
      component: '4nm AI Accelerators',
      quantity: 5000,
      capacity: 6000,
      budget: 20000,
      slaDays: 7,
      shippingMode: 'Second Class',
      scheduledDays: 2,
      simulatedDelay: 14,
      region: 'Southeast Asia'
    },
    presetCritical: {
      id: 'CHIP-CRIT-9921',
      component: 'Automotive Grade MCUs',
      quantity: 3000,
      capacity: 5000,
      budget: 25000,
      slaDays: 3,
      shippingMode: 'First Class',
      scheduledDays: 1,
      simulatedDelay: 12,
      region: 'East Asia'
    },
    presetBudget: {
      id: 'CHIP-BUDGET-401',
      component: 'Power Management ICs',
      quantity: 2000,
      capacity: 4000,
      budget: 10000,
      slaDays: 5,
      shippingMode: 'Second Class',
      scheduledDays: 2,
      simulatedDelay: 8,
      region: 'Taiwan'
    },
    presetInfeasible: {
      id: 'CHIP-OVER-500',
      component: 'Mobile RF Transceivers',
      quantity: 7500,
      capacity: 5000,
      budget: 30000,
      slaDays: 7,
      shippingMode: 'Standard Class',
      scheduledDays: 4,
      simulatedDelay: 14,
      region: 'Pacific Asia'
    }
  };

  Object.entries(presets).forEach(([btnId, data]) => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener('click', () => {
        document.getElementById('shipmentId').value = data.id;
        document.getElementById('componentName').value = data.component;
        document.getElementById('requiredQuantity').value = data.quantity;
        document.getElementById('supplierCapacity').value = data.capacity;
        document.getElementById('budgetInput').value = data.budget;
        document.getElementById('maxDeliveryDays').value = data.slaDays;
        document.getElementById('shippingMode').value = data.shippingMode;
        document.getElementById('scheduledDays').value = data.scheduledDays;
        document.getElementById('simulatedDelay').value = data.simulatedDelay;
        document.getElementById('orderRegion').value = data.region;

        showToast(`Loaded preset: ${btn.textContent}`, 'success');
      });
    }
  });
}

// ============================================================================
// Form Submissions & API Actions
// ============================================================================
function getFormData() {
  return {
    shipment_id: document.getElementById('shipmentId').value.trim() || 'SHP001',
    component: document.getElementById('componentName').value.trim() || 'Microchips',
    required_quantity: parseInt(document.getElementById('requiredQuantity').value, 10) || 5000,
    supplier_capacity: parseInt(document.getElementById('supplierCapacity').value, 10) || 6000,
    budget: parseFloat(document.getElementById('budgetInput').value) || 20000.0,
    max_delivery_days: parseInt(document.getElementById('maxDeliveryDays').value, 10) || 7,
    shipping_mode: document.getElementById('shippingMode').value,
    scheduled_days: parseInt(document.getElementById('scheduledDays').value, 10) || 2,
    simulated_delay_days: parseInt(document.getElementById('simulatedDelay').value, 10) || 14,
    order_region: document.getElementById('orderRegion').value.trim() || 'Southeast Asia',
    // Dataset feature aliases matching ML model expectations
    'Days for shipment (scheduled)': parseInt(document.getElementById('scheduledDays').value, 10) || 2,
    'Shipping Mode': document.getElementById('shippingMode').value,
    'Order Item Quantity': parseInt(document.getElementById('requiredQuantity').value, 10) || 5000,
    'Order Region': document.getElementById('orderRegion').value.trim() || 'Southeast Asia',
    'Customer Segment': 'Corporate',
    'Market': 'Pacific Asia',
    'Order Country': 'Taiwan'
  };
}

function initFormHandlers() {
  // 1. Standalone ML Delay Prediction
  const btnPredict = document.getElementById('btnRunPrediction');
  if (btnPredict) {
    btnPredict.addEventListener('click', async () => {
      const payload = getFormData();
      btnPredict.disabled = true;
      btnPredict.innerHTML = '<span>⏳</span> Analyzing Risk...';
      try {
        const res = await fetch(`${API_BASE}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderPrediction(data);
        showToast(`ML Prediction complete for ${data.shipment_id}`, 'success');
      } catch (err) {
        showToast(`Prediction failed: ${err.message}`, 'error');
      } finally {
        btnPredict.disabled = false;
        btnPredict.innerHTML = '<span>🔍</span> Run ML Delay Prediction';
      }
    });
  }

  // 2. Full Closed-Loop Prescriptive Optimization
  const form = document.getElementById('prescriptionForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = getFormData();
      const btnSubmit = document.getElementById('btnRunPrescription');
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span>⏳</span> Solving PuLP LP...';
      try {
        const res = await fetch(`${API_BASE}/prescribe`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        currentPrescription = data;
        renderPrescription(data, payload);
        showToast(`Prescriptive Optimization solved! Action: ${data.optimization.recommended_action || 'Infeasible'}`, 'success');
      } catch (err) {
        showToast(`Optimization failed: ${err.message}`, 'error');
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<span>⚡</span> Execute Prescriptive Optimization';
      }
    });
  }

  // 3. Manager Decision Write-Back
  const btnRecordDecision = document.getElementById('btnRecordDecision');
  if (btnRecordDecision) {
    btnRecordDecision.addEventListener('click', async () => {
      const shipmentId = document.getElementById('shipmentId').value.trim();
      const selectedRadio = document.querySelector('input[name="manager_choice"]:checked');
      if (!selectedRadio) {
        showToast('Please select a decision action first.', 'error');
        return;
      }
      const managerDecision = selectedRadio.value;
      const notes = document.getElementById('managerNotes').value.trim();

      btnRecordDecision.disabled = true;
      try {
        const res = await fetch(`${API_BASE}/decision`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            shipment_id: shipmentId,
            manager_decision: managerDecision,
            notes: notes || `Approved ${managerDecision}`
          })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        showToast(data.message, 'success');
      } catch (err) {
        showToast(`Failed to record decision: ${err.message}`, 'error');
      } finally {
        btnRecordDecision.disabled = false;
      }
    });
  }

  // 4. Post-Delivery Outcome Logging
  const btnRecordOutcome = document.getElementById('btnRecordOutcome');
  if (btnRecordOutcome) {
    btnRecordOutcome.addEventListener('click', async () => {
      const shipmentId = document.getElementById('shipmentId').value.trim();
      const actualDays = parseInt(document.getElementById('actualDays').value, 10) || 2;
      const actualCost = parseFloat(document.getElementById('actualCost').value) || 15000.0;
      const decisionEffective = parseInt(document.getElementById('decisionEffective').value, 10);
      const feedbackNotes = document.getElementById('feedbackNotes').value.trim();

      btnRecordOutcome.disabled = true;
      try {
        const res = await fetch(`${API_BASE}/outcome`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            shipment_id: shipmentId,
            actual_delivery_days: actualDays,
            actual_cost: actualCost,
            delay_occurred: actualDays > 7 ? 1 : 0,
            decision_effective: decisionEffective,
            feedback_notes: feedbackNotes
          })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        showToast(data.message, 'success');
      } catch (err) {
        showToast(`Failed to record outcome: ${err.message}`, 'error');
      } finally {
        btnRecordOutcome.disabled = false;
      }
    });
  }
}

// ============================================================================
// Renderers
// ============================================================================
function renderPrediction(data) {
  const prob = data.delay_probability;
  const pct = Math.round(prob * 100);
  const days = data.predicted_delay_days;

  const scoreText = document.getElementById('riskScoreText');
  const levelLabel = document.getElementById('riskLevelLabel');
  const delayText = document.getElementById('predictedDelayText');
  const meterFill = document.getElementById('meterFill');
  const badge = document.getElementById('mlStatusBadge');

  scoreText.textContent = `${pct}%`;
  delayText.textContent = `${days} Days`;
  meterFill.style.width = `${pct}%`;

  scoreText.className = 'risk-score';
  meterFill.className = 'meter-fill';

  if (prob >= 0.6) {
    scoreText.classList.add('high');
    meterFill.classList.add('high');
    levelLabel.textContent = 'HIGH DELAY RISK';
    badge.textContent = 'High Delay Risk';
    badge.className = 'card-badge amber';
  } else if (prob >= 0.4) {
    scoreText.classList.add('medium');
    meterFill.classList.add('medium');
    levelLabel.textContent = 'MODERATE RISK';
    badge.textContent = 'Moderate Risk';
    badge.className = 'card-badge cyan';
  } else {
    scoreText.classList.add('low');
    meterFill.classList.add('low');
    levelLabel.textContent = 'ON-TIME PROBABLE';
    badge.textContent = 'Low Risk';
    badge.className = 'card-badge emerald';
  }

  document.getElementById('metaStatus').textContent = `${days > 0 ? days + 'd Delay' : 'On Schedule'}`;
}

function renderPrescription(data, inputPayload) {
  renderPrediction(data.prediction);

  const opt = data.optimization;
  const optBadge = document.getElementById('optStatusBadge');
  const actionName = document.getElementById('recommendedActionName');
  const statusMsg = document.getElementById('recommendationStatusMsg');
  const costVal = document.getElementById('recCostValue');
  const daysVal = document.getElementById('recDaysValue');
  const tbody = document.getElementById('optionsTableBody');
  const pillGroup = document.getElementById('decisionPillGroup');

  optBadge.textContent = opt.status;
  if (opt.status === 'Optimal') {
    optBadge.className = 'card-badge emerald';
    actionName.textContent = opt.recommended_action;
    statusMsg.textContent = `PuLP linear solver found optimal mitigation satisfying budget ($${inputPayload.budget.toLocaleString()}) and SLA (${inputPayload.max_delivery_days} days).`;

    const chosen = opt.chosen_option || (opt.options && opt.options[opt.recommended_action]) || {};
    costVal.textContent = `$${(chosen.cost || 0).toLocaleString()}`;
    daysVal.textContent = `${chosen.delivery_days || 0} Days`;
  } else {
    optBadge.className = 'card-badge amber';
    actionName.textContent = 'No Feasible Action';
    statusMsg.textContent = opt.message || 'Constraints violated (e.g. quantity exceeds capacity or budget too tight).';
    costVal.textContent = '$0';
    daysVal.textContent = 'N/A';
  }

  // Render Alternatives Table
  tbody.innerHTML = '';
  pillGroup.innerHTML = '';

  const options = opt.options || {};
  Object.entries(options).forEach(([name, details]) => {
    const isSelected = opt.recommended_action === name;
    const meetsSla = details.delivery_days <= inputPayload.max_delivery_days;
    const meetsBudget = details.cost <= inputPayload.budget;

    const row = document.createElement('tr');
    if (isSelected) row.classList.add('selected-row');

    row.innerHTML = `
      <td>
        <strong>${name}</strong>
        ${isSelected ? '<span style="font-size: 0.72rem; color: var(--emerald); margin-left: 0.4rem;">[RECOMMENDED]</span>' : ''}
      </td>
      <td style="color: #38bdf8; font-weight: 600;">$${details.cost.toLocaleString()}</td>
      <td>${details.delivery_days} Days</td>
      <td>
        <span class="${meetsSla ? 'tag-sla-pass' : 'tag-sla-fail'}">
          ${meetsSla ? '✔ Pass' : `✖ Exceeds SLA (${details.delivery_days}d > ${inputPayload.max_delivery_days}d)`}
        </span>
      </td>
      <td>
        <span class="${meetsBudget ? 'tag-sla-pass' : 'tag-sla-fail'}">
          ${meetsBudget ? '✔ Within Budget' : '✖ Exceeds Budget'}
        </span>
      </td>
    `;
    tbody.appendChild(row);

    // Decision Pills
    const radioId = `choice_${name.replace(/\s+/g, '_')}`;
    const pillWrapper = document.createElement('div');
    pillWrapper.style.display = 'contents';
    pillWrapper.innerHTML = `
      <input type="radio" id="${radioId}" name="manager_choice" value="${name}" class="radio-pill-input" ${isSelected ? 'checked' : ''}>
      <label for="${radioId}" class="radio-pill-label">${name}</label>
    `;
    pillGroup.appendChild(pillWrapper);
  });
}

// ============================================================================
// Audit Trail & Database Querying
// ============================================================================
async function loadAuditTrail() {
  try {
    const [analyticsRes, decisionsRes, outcomesRes] = await Promise.all([
      fetch(`${API_BASE}/analytics`),
      fetch(`${API_BASE}/history/decisions`),
      fetch(`${API_BASE}/history/outcomes`)
    ]);

    if (analyticsRes.ok) {
      const a = await analyticsRes.json();
      document.getElementById('kpiTotalShipments').textContent = a.total_shipments_tracked || 0;
      document.getElementById('kpiAvgRisk').textContent = `${Math.round((a.average_delay_probability || 0) * 100)}%`;
      document.getElementById('kpiOptimalCount').textContent = a.optimal_solutions_found || 0;
      document.getElementById('kpiEffectiveness').textContent = `${a.decision_effectiveness_pct || 100}%`;
    }

    if (decisionsRes.ok) {
      const decisions = await decisionsRes.json();
      const tbody = document.getElementById('decisionsTableBody');
      if (decisions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No decisions logged in SQLite yet.</td></tr>`;
      } else {
        tbody.innerHTML = decisions.map(d => `
          <tr>
            <td><strong>${d.shipment_id}</strong></td>
            <td>${d.required_quantity}</td>
            <td>$${Number(d.budget).toLocaleString()}</td>
            <td>${d.max_delivery_days}d</td>
            <td style="color: var(--cyan); font-weight: 600;">${d.recommended_action || 'None'}</td>
            <td style="color: var(--emerald); font-weight: 600;">${d.manager_decision || 'Pending'}</td>
            <td><span class="card-badge ${d.optimization_status === 'Optimal' ? 'emerald' : 'amber'}">${d.optimization_status}</span></td>
            <td style="font-size: 0.75rem;">${d.created_at || 'Just now'}</td>
          </tr>
        `).join('');
      }
    }

    if (outcomesRes.ok) {
      const outcomes = await outcomesRes.json();
      const tbody = document.getElementById('outcomesTableBody');
      if (outcomes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No post-delivery outcomes recorded yet.</td></tr>`;
      } else {
        tbody.innerHTML = outcomes.map(o => `
          <tr>
            <td><strong>${o.shipment_id}</strong></td>
            <td>${o.actual_delivery_days} Days</td>
            <td>$${Number(o.actual_cost).toLocaleString()}</td>
            <td>${o.delay_occurred ? '⚠️ Yes' : '✔ No'}</td>
            <td>${o.decision_effective ? '<span style="color: var(--emerald);">✔ Effective</span>' : '<span style="color: var(--rose);">✖ Failed</span>'}</td>
            <td>${o.feedback_notes || 'No feedback notes'}</td>
            <td style="font-size: 0.75rem;">${o.recorded_at || 'Just now'}</td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    showToast(`Could not refresh audit trail: ${err.message}`, 'error');
  }
}

// ============================================================================
// ML Model Metrics Loading
// ============================================================================
async function loadMlMetrics() {
  try {
    const res = await fetch(`${API_BASE}/ml/metrics`);
    if (res.ok) {
      const data = await res.json();
      if (data.accuracy) {
        document.getElementById('mlMetricAcc').textContent = `${(data.accuracy * 100).toFixed(2)}%`;
      }
      if (data.precision) {
        document.getElementById('mlMetricPrec').textContent = `${(data.precision * 100).toFixed(2)}%`;
      }
      if (data.f1_score) {
        document.getElementById('mlMetricF1').textContent = data.f1_score.toFixed(4);
      }
      if (data.roc_auc) {
        document.getElementById('mlMetricAuc').textContent = data.roc_auc.toFixed(4);
      }
    }
  } catch (err) {
    console.warn('Could not load ML metrics:', err);
  }
}

// ============================================================================
// Toast Notification Utility
// ============================================================================
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✔' : '✖'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
