/**
 * SupplyPrescript — Swiss Minimalist Application Controller
 * Inspired by Basel Ink / Swiss International Typographic Style
 * Preserves 100% of existing functionality, endpoints, and data bindings.
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
  const dot = badge ? badge.querySelector('.status-dot') : null;

  try {
    const res = await fetch(`${API_BASE}/`);
    if (res.ok) {
      if (text) text.textContent = 'Operational (FastAPI Live)';
      if (dot) dot.classList.remove('offline');
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    if (text) text.textContent = 'Backend Offline';
    if (dot) dot.classList.add('offline');
  }
}

// ============================================================================
// 5-Stage Closed-Loop Workflow Stepper Sync
// ============================================================================
function updateWorkflowStepper(activeStep) {
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`step${i}`);
    if (el) {
      if (i <= activeStep) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    }
  }
}

// ============================================================================
// Website Tab Navigation System with Topbar Breadcrumb Sync
// ============================================================================
const TAB_BREADCRUMBS = {
  'tab-home': 'OVERVIEW',
  'tab-console': 'DECISION CONSOLE',
  'tab-audit': 'AUDIT LEDGER',
  'tab-ml': 'MODEL & INTEGRITY',
  'tab-about': 'ABOUT'
};

function switchTab(targetId) {
  // 1. Sync sidebar nav link active states
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    if (btn.getAttribute('data-tab') === targetId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 2. Switch visible canvas view
  document.querySelectorAll('.tab-content').forEach(content => {
    if (content.id === targetId) {
      content.classList.remove('hidden');
    } else {
      content.classList.add('hidden');
    }
  });

  // 3. Update topbar breadcrumb label
  const breadcrumbEl = document.getElementById('topbarCurrentView');
  if (breadcrumbEl && TAB_BREADCRUMBS[targetId]) {
    breadcrumbEl.textContent = TAB_BREADCRUMBS[targetId];
  }

  // 4. Update topbar action button behavior
  const topActionBtn = document.getElementById('navLaunchConsoleBtn');
  if (topActionBtn) {
    if (targetId === 'tab-console') {
      topActionBtn.innerHTML = `
        <span>Solve Mitigation</span>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
      `;
    } else {
      topActionBtn.innerHTML = `
        <span>Open Console</span>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <polyline points="12 5 19 12 12 19"></polyline>
        </svg>
      `;
    }
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Load audit trail dynamically when navigating to audit view
  if (targetId === 'tab-audit') {
    loadAuditTrail();
  }
}

function initTabNavigation() {
  // Sidebar Tab Buttons
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-tab');
      if (targetId) switchTab(targetId);
    });
  });

  // Brand Logo Click -> Goes to Overview
  const brandHomeLink = document.getElementById('brandHomeLink');
  if (brandHomeLink) {
    brandHomeLink.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab('tab-home');
    });
  }

  // Topbar Action Button -> Triggers optimization in Console or switches to Console
  const topActionBtn = document.getElementById('navLaunchConsoleBtn');
  if (topActionBtn) {
    topActionBtn.addEventListener('click', () => {
      const consoleView = document.getElementById('tab-console');
      const isConsoleActive = consoleView && !consoleView.classList.contains('hidden');
      
      if (isConsoleActive) {
        // If already in console, trigger form submit
        const form = document.getElementById('prescriptionForm');
        if (form) form.requestSubmit();
      } else {
        // Otherwise switch to Console
        switchTab('tab-console');
      }
    });
  }

  // Home Callout Button -> Switch to Console
  const homeCalloutBtn = document.getElementById('homeCalloutBtn');
  if (homeCalloutBtn) {
    homeCalloutBtn.addEventListener('click', () => switchTab('tab-console'));
  }

  // Hero Section Action Buttons
  const heroLaunchBtn = document.getElementById('heroLaunchBtn');
  if (heroLaunchBtn) {
    heroLaunchBtn.addEventListener('click', () => switchTab('tab-console'));
  }

  const heroAuditBtn = document.getElementById('heroAuditBtn');
  if (heroAuditBtn) {
    heroAuditBtn.addEventListener('click', () => switchTab('tab-audit'));
  }

  const heroMlBtn = document.getElementById('heroMlBtn');
  if (heroMlBtn) {
    heroMlBtn.addEventListener('click', () => switchTab('tab-ml'));
  }

  // Back to Homepage Buttons
  document.querySelectorAll('.back-to-home').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab('tab-home');
    });
  });

  // Audit Refresh Button
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

        updateWorkflowStepper(1);
        showToast(`Loaded: ${btn.textContent.trim()}`, 'success');
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
      btnPredict.innerHTML = '<span class="btn-spinner"></span> <span>Evaluating Risk...</span>';
      try {
        const res = await fetch(`${API_BASE}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderPrediction(data);
        updateWorkflowStepper(2);
        showToast(`Disruption evaluated: ${data.shipment_id}`, 'success');
      } catch (err) {
        showToast(`Prediction failed: ${err.message}`, 'error');
      } finally {
        btnPredict.disabled = false;
        btnPredict.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <span>Evaluate Risk (ML Only)</span>
        `;
      }
    });
  }

  // 2. Full Closed-Loop Prescriptive Optimization (THE KEY ACTION)
  const form = document.getElementById('prescriptionForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = getFormData();
      const btnSubmit = document.getElementById('btnRunPrescription');
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span class="btn-spinner"></span> <span>Solving PuLP MILP...</span>';
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
        updateWorkflowStepper(3);
        showToast(`Optimal policy: ${data.optimization.recommended_action || 'Infeasible'}`, 'success');
      } catch (err) {
        showToast(`Optimization failed: ${err.message}`, 'error');
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
          <span>Solve Prescriptive Mitigation (PuLP)</span>
        `;
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
        showToast('Please select an authorized mitigation action first.', 'error');
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
        updateWorkflowStepper(4);
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
        updateWorkflowStepper(5);
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
// Renderers (Clean Swiss Layout)
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

  if (scoreText) scoreText.textContent = `${pct}%`;
  if (delayText) delayText.textContent = `${days} Days`;
  if (meterFill) meterFill.style.width = `${pct}%`;

  if (prob >= 0.6) {
    if (levelLabel) levelLabel.textContent = 'HIGH DISRUPTION RISK';
    if (badge) badge.textContent = 'High Delay Risk';
  } else if (prob >= 0.4) {
    if (levelLabel) levelLabel.textContent = 'MODERATE DISRUPTION RISK';
    if (badge) badge.textContent = 'Moderate Risk';
  } else {
    if (levelLabel) levelLabel.textContent = 'ON-TIME DISPATCH PROBABLE';
    if (badge) badge.textContent = 'Low Risk';
  }

  const metaStatus = document.getElementById('metaStatus');
  if (metaStatus) {
    metaStatus.textContent = `${days > 0 ? days + 'd Delay' : 'On Schedule'}`;
  }
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

  if (optBadge) {
    optBadge.textContent = opt.status;
  }

  if (opt.status === 'Optimal') {
    if (actionName) actionName.textContent = opt.recommended_action;
    if (statusMsg) {
      statusMsg.textContent = `PuLP solver identified optimal mitigation satisfying budget ($${inputPayload.budget.toLocaleString()}) and SLA (${inputPayload.max_delivery_days} days).`;
    }

    const chosen = opt.chosen_option || (opt.options && opt.options[opt.recommended_action]) || {};
    if (costVal) costVal.textContent = `$${(chosen.cost || 0).toLocaleString()}`;
    if (daysVal) daysVal.textContent = `${chosen.delivery_days || 0} Days`;
  } else {
    if (actionName) actionName.textContent = 'No Feasible Mitigation Found';
    if (statusMsg) {
      statusMsg.textContent = opt.message || 'Constraints violated (e.g. required volume exceeds fab capacity or budget threshold exceeded).';
    }
    if (costVal) costVal.textContent = '$0';
    if (daysVal) daysVal.textContent = 'N/A';
  }

  // Render Alternatives Table in Clean Swiss Style
  if (tbody) tbody.innerHTML = '';
  if (pillGroup) pillGroup.innerHTML = '';

  const options = opt.options || {};
  Object.entries(options).forEach(([name, details]) => {
    const isSelected = opt.recommended_action === name;
    const meetsSla = details.delivery_days <= inputPayload.max_delivery_days;
    const meetsBudget = details.cost <= inputPayload.budget;

    if (tbody) {
      const row = document.createElement('tr');
      if (isSelected) row.classList.add('selected-row');

      row.innerHTML = `
        <td>
          <strong>${name}</strong>
          ${isSelected ? '<span style="font-size: 10px; color: #1d4ed8; background: #dbeafe; padding: 2px 6px; border-radius: 2px; margin-left: 6px; font-weight: 700;">OPTIMAL</span>' : ''}
        </td>
        <td class="mono" style="font-weight: 600;">$${details.cost.toLocaleString()}</td>
        <td class="mono">${details.delivery_days} Days</td>
        <td>
          <span class="${meetsSla ? 'tag-sla-pass' : 'tag-sla-fail'}">
            ${meetsSla ? 'Within SLA' : `Exceeds SLA (${details.delivery_days}d > ${inputPayload.max_delivery_days}d)`}
          </span>
        </td>
        <td>
          <span class="${meetsBudget ? 'tag-sla-pass' : 'tag-sla-fail'}">
            ${meetsBudget ? 'Within Budget' : 'Exceeds Budget'}
          </span>
        </td>
      `;
      tbody.appendChild(row);
    }

    // Decision Pills
    if (pillGroup) {
      const radioId = `choice_${name.replace(/\s+/g, '_')}`;
      const pillWrapper = document.createElement('div');
      pillWrapper.style.display = 'contents';
      pillWrapper.innerHTML = `
        <input type="radio" id="${radioId}" name="manager_choice" value="${name}" class="radio-pill-input" ${isSelected ? 'checked' : ''}>
        <label for="${radioId}" class="radio-pill-label">${name}</label>
      `;
      pillGroup.appendChild(pillWrapper);
    }
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
      const kpiTotal = document.getElementById('kpiTotalShipments');
      const kpiRisk = document.getElementById('kpiAvgRisk');
      const kpiOpt = document.getElementById('kpiOptimalCount');
      const kpiEff = document.getElementById('kpiEffectiveness');

      if (kpiTotal) kpiTotal.textContent = a.total_shipments_tracked || 0;
      if (kpiRisk) kpiRisk.textContent = `${Math.round((a.average_delay_probability || 0) * 100)}%`;
      if (kpiOpt) kpiOpt.textContent = a.optimal_solutions_found || 0;
      if (kpiEff) kpiEff.textContent = `${a.decision_effectiveness_pct || 100}%`;
    }

    if (decisionsRes.ok) {
      const decisions = await decisionsRes.json();
      const tbody = document.getElementById('decisionsTableBody');
      if (tbody) {
        if (decisions.length === 0) {
          tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No prescriptive decisions recorded in SQLite ledger yet.</td></tr>`;
        } else {
          tbody.innerHTML = decisions.map(d => `
            <tr>
              <td><strong>${d.shipment_id}</strong></td>
              <td class="mono">${d.required_quantity}</td>
              <td class="mono">$${Number(d.budget).toLocaleString()}</td>
              <td class="mono">${d.max_delivery_days}d</td>
              <td>${d.recommended_action || 'None'}</td>
              <td><strong>${d.manager_decision || 'Pending'}</strong></td>
              <td><span class="swiss-badge">${d.optimization_status}</span></td>
              <td class="mono" style="font-size: 11.5px; color: var(--text-muted);">${d.created_at || 'Just now'}</td>
            </tr>
          `).join('');
        }
      }
    }

    if (outcomesRes.ok) {
      const outcomes = await outcomesRes.json();
      const tbody = document.getElementById('outcomesTableBody');
      if (tbody) {
        if (outcomes.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">No outcomes logged yet.</td></tr>`;
        } else {
          tbody.innerHTML = outcomes.map(o => `
            <tr>
              <td><strong>${o.shipment_id}</strong></td>
              <td class="mono">${o.actual_delivery_days} Days</td>
              <td class="mono">$${Number(o.actual_cost).toLocaleString()}</td>
              <td>${o.delay_occurred ? '<span class="tag-sla-fail">Delayed</span>' : '<span class="tag-sla-pass">On-Time</span>'}</td>
              <td>${o.decision_effective ? '<span class="tag-sla-pass">Effective</span>' : '<span class="tag-sla-fail">Ineffective</span>'}</td>
              <td>${o.feedback_notes || 'No feedback notes'}</td>
              <td class="mono" style="font-size: 11.5px; color: var(--text-muted);">${o.recorded_at || 'Just now'}</td>
            </tr>
          `).join('');
        }
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
      const acc = document.getElementById('mlMetricAcc');
      const prec = document.getElementById('mlMetricPrec');
      const f1 = document.getElementById('mlMetricF1');
      const auc = document.getElementById('mlMetricAuc');

      if (acc && data.accuracy) acc.textContent = `${(data.accuracy * 100).toFixed(2)}%`;
      if (prec && data.precision) prec.textContent = `${(data.precision * 100).toFixed(2)}%`;
      if (f1 && data.f1_score) f1.textContent = data.f1_score.toFixed(4);
      if (auc && data.roc_auc) auc.textContent = data.roc_auc.toFixed(4);
    }
  } catch (err) {
    console.warn('Could not load ML metrics:', err);
  }
}

// ============================================================================
// Toast Notification Utility (Clean Swiss Minimalist)
// ============================================================================
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-dot"></span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(6px)';
    setTimeout(() => toast.remove(), 180);
  }, 2600);
}
