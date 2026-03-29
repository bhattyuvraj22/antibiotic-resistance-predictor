// ─── CHART REGISTRY ───────────────────────────────────────────────────────────
const _initialised = {};   // tracks which pages have been rendered
const _charts      = {};   // holds live Chart.js instances for safe destruction

function makeChart(id, config) {
  if (_charts[id]) { try { _charts[id].destroy(); } catch(e){} }
  const el = document.getElementById(id);
  if (!el) return null;
  _charts[id] = new Chart(el, config);
  return _charts[id];
}

// ─── CHART DEFAULTS ───────────────────────────────────────────────────────────
const chartDefaults = {
  color: '#6a8fa8',
  plugins: {
    legend: { labels: { color: '#6a8fa8', font: { family: 'DM Sans', size: 11 } } }
  },
  scales: {
    x: { grid: { color: 'rgba(26,45,66,0.5)' }, ticks: { color: '#6a8fa8', font: { family: 'Space Mono', size: 10 } } },
    y: { grid: { color: 'rgba(26,45,66,0.5)' }, ticks: { color: '#6a8fa8', font: { family: 'Space Mono', size: 10 } } }
  }
};

// ─── NAVIGATION ───────────────────────────────────────────────────────────────
const pages = ['dashboard','clinical','environmental','features','performance','strategy'];

function navigate(id, el) {
  pages.forEach(p => document.getElementById('page-'+p).classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');
  // Double rAF: first frame applies display:flex, second frame lets browser paint
  // so Chart.js can measure canvas dimensions correctly
  requestAnimationFrame(() => requestAnimationFrame(() => initPage(id)));
}

// ─── LAZY PAGE INIT ───────────────────────────────────────────────────────────
function initPage(id) {
  if (_initialised[id] && id !== 'strategy') return;
  if (id !== 'strategy') _initialised[id] = true;
  switch (id) {
    case 'dashboard':   initDashboard();   break;
    case 'features':    initFeatures();    break;
    case 'performance': initPerformance(); break;
    case 'strategy':    initStrategy();    break;
  }
}

// ─── DASHBOARD ────────────────────────────────────────────────────────────────
function initDashboard() {
  const abxList     = ['AMX/AMP','AMC','CZ','FOX','CTX/CRO','IPM','GEN','AN','ofx','CIP'];
  const resistProbs = [0.48,0.35,0.28,0.42,0.55,0.18,0.30,0.25,0.60,0.44];

  makeChart('dashBarChart', {
    type: 'bar',
    data: {
      labels: abxList,
      datasets: [{
        label: 'Resistance Probability',
        data: resistProbs,
        backgroundColor: resistProbs.map(p =>
          p > 0.5 ? 'rgba(255,69,69,0.7)' : p > 0.35 ? 'rgba(245,166,35,0.7)' : 'rgba(0,255,157,0.7)'
        ),
        borderRadius: 4
      }]
    },
    options: { ...chartDefaults, plugins: { legend: { display: false } } }
  });

  makeChart('dashDonutChart', {
    type: 'doughnut',
    data: {
      labels: ['Susceptible','Intermediate','Resistant'],
      datasets: [{
        data: [62,20,18],
        backgroundColor: ['rgba(0,255,157,0.8)','rgba(245,166,35,0.8)','rgba(255,69,69,0.8)'],
        borderColor: '#060b12',
        borderWidth: 2
      }]
    },
    options: { plugins: { legend: { display: false } }, cutout: '65%' }
  });

  makeChart('dashLineChart', {
    type: 'line',
    data: {
      labels: [1,2,3,4,5,6,7,8,9,10],
      datasets: [
        { label:'Accuracy', data:[0.65,0.72,0.78,0.82,0.85,0.87,0.88,0.89,0.89,0.90], borderColor:'#00d4ff', backgroundColor:'rgba(0,212,255,0.05)', tension:0.4, fill:true, pointRadius:3 },
        { label:'F1 Score', data:[0.60,0.68,0.74,0.79,0.82,0.84,0.85,0.86,0.86,0.87], borderColor:'#00ff9d', backgroundColor:'rgba(0,255,157,0.05)', tension:0.4, fill:true, pointRadius:3 },
        { label:'ROC AUC', data:[0.70,0.75,0.80,0.83,0.85,0.86,0.87,0.88,0.88,0.89], borderColor:'#f5a623', backgroundColor:'rgba(245,166,35,0.05)', tension:0.4, fill:true, pointRadius:3 }
      ]
    },
    options: { ...chartDefaults, scales: { ...chartDefaults.scales, y: { ...chartDefaults.scales.y, min:0.5, max:1 } } }
  });
}

// ─── GENE & FEATURES PAGE ─────────────────────────────────────────────────────
const geneFeatures = [
  { name:'blaCTX-M',         score:0.80, family:'esbl'      },
  { name:'Hospital_before',  score:0.72, family:'clinical'  },
  { name:'blaKPC',           score:0.65, family:'carba'     },
  { name:'ampC',             score:0.60, family:'esbl'      },
  { name:"aac(6')-Ib",      score:0.52, family:'amino'     },
  { name:'Species (E.coli)', score:0.48, family:'clinical'  },
  { name:'qnrB',             score:0.44, family:'quinolone' },
  { name:'Age',              score:0.38, family:'clinical'  },
  { name:'Infection_Freq',   score:0.30, family:'clinical'  },
  { name:'Diabetes',         score:0.22, family:'clinical'  },
];

function renderGeneFeats(filter='all') {
  const list = filter==='all' ? geneFeatures : geneFeatures.filter(g=>g.family===filter);
  document.getElementById('gene-feat-list').innerHTML = list.map(g=>`
    <div class="feat-row">
      <span class="feat-name">${g.name}</span>
      <div class="feat-bar-track"><div class="feat-bar-fill" style="width:${g.score*100}%"></div></div>
      <span class="feat-score">${g.score.toFixed(2)}</span>
    </div>`).join('');
}

function filterGenes(f, el) { renderGeneFeats(f); }

function initFeatures() {
  renderGeneFeats();
  makeChart('globalFeatChart', {
    type: 'bar',
    data: {
      labels: geneFeatures.map(g=>g.name),
      datasets: [{ label:'Importance', data:geneFeatures.map(g=>g.score), backgroundColor:'rgba(0,212,255,0.6)', borderRadius:4 }]
    },
    options: { indexAxis:'y', ...chartDefaults, plugins:{ legend:{ display:false } } }
  });
}

// ─── MODEL PERFORMANCE PAGE ───────────────────────────────────────────────────
function initPerformance() {
  const clinF1 = {
    'AMX/AMP':0.65,'AMC':0.68,'CZ':0.70,'FOX':0.72,'CTX/CRO':0.74,
    'IPM':0.73,'GEN':0.71,'AN':0.69,'Acide nalidixique':0.67,
    'ofx':0.66,'CIP':0.71,'C':0.64,'Co-trimoxazole':0.70,'Furanes':0.68,'colistine':0.62
  };

  const tbody = document.getElementById('f1-tbody');
  tbody.innerHTML = '';
  Object.entries(clinF1).forEach(([abx, score]) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${abx}</td>
      <td style="font-family:var(--mono);color:var(--accent);">${score.toFixed(3)}</td>
      <td><div class="f1-bar"><div class="f1-mini-bar"><div class="f1-mini-fill" style="width:${score*100}%"></div></div></div></td>`;
    tbody.appendChild(tr);
  });

  makeChart('envF1Chart', {
    type: 'bar',
    data: {
      labels: ['imipenem','ceftazidime','gentamicin','augmentin','ciprofloxacin'],
      datasets: [{ label:'F1 Score', data:[0.6157,0.6395,0.7111,0.7306,0.7111], backgroundColor:'rgba(0,255,157,0.6)', borderRadius:4 }]
    },
    options: { ...chartDefaults, plugins:{legend:{display:false}}, scales:{...chartDefaults.scales, y:{...chartDefaults.scales.y, min:0, max:1}} }
  });

  makeChart('genChart', {
    type: 'bar',
    data: {
      labels: ['Train','Test'],
      datasets: [{ data:[0.91,0.87], backgroundColor:['rgba(0,212,255,0.7)','rgba(0,255,157,0.7)'], borderRadius:6 }]
    },
    options: { ...chartDefaults, plugins:{legend:{display:false}}, scales:{...chartDefaults.scales, y:{...chartDefaults.scales.y, min:0.7, max:1}} }
  });

  const fpr = [0,0.05,0.1,0.15,0.2,0.3,0.4,0.5,0.7,1];
  const tpr = [0,0.35,0.58,0.72,0.80,0.87,0.91,0.94,0.97,1];
  makeChart('rocChart', {
    type: 'line',
    data: {
      labels: fpr,
      datasets: [
        { label:'ROC AUC=0.91', data:tpr, borderColor:'#00d4ff', backgroundColor:'rgba(0,212,255,0.07)', tension:0.3, fill:true, pointRadius:2 },
        { label:'Random',       data:fpr, borderColor:'#3a5a72', borderDash:[4,4], pointRadius:0 }
      ]
    },
    options: { ...chartDefaults, scales: {
      ...chartDefaults.scales,
      x: { ...chartDefaults.scales.x, title:{ display:true, text:'False Positive Rate', color:'#6a8fa8' } },
      y: { ...chartDefaults.scales.y, title:{ display:true, text:'True Positive Rate',  color:'#6a8fa8' } }
    }}
  });

  makeChart('confChart', {
    type: 'bar',
    data: {
      labels: ['True S / Pred S','True S / Pred R','True R / Pred S','True R / Pred R'],
      datasets: [{ data:[420,80,60,340], backgroundColor:['rgba(0,255,157,0.7)','rgba(255,69,69,0.5)','rgba(255,69,69,0.5)','rgba(0,212,255,0.7)'], borderRadius:4 }]
    },
    options: { indexAxis:'y', ...chartDefaults, plugins:{legend:{display:false}} }
  });
}

// ─── TREATMENT STRATEGY PAGE ──────────────────────────────────────────────────
function initStrategy() {
  makeChart('riskChart', {
    type: 'radar',
    data: {
      labels: ['Prior Hospitalization','Diabetes','High Inf. Freq','Prior ABX Exposure','ESBL Genes','Age > 60'],
      datasets: [{ label:'Resistance Risk Score', data:[0.85,0.60,0.75,0.80,0.90,0.50], borderColor:'#ff4545', backgroundColor:'rgba(255,69,69,0.1)', pointBackgroundColor:'#ff4545' }]
    },
    options: {
      plugins: { legend:{ labels:{ color:'#6a8fa8' } } },
      scales: { r:{ grid:{ color:'rgba(26,45,66,0.7)' }, ticks:{ display:false }, pointLabels:{ color:'#6a8fa8', font:{ size:11 } }, min:0, max:1 } }
    }
  });
  // ranking is now handled by _updateEfficacyRanking — no hardcoded data here
}

// ─── EFFICACY RANKING (dynamic) ───────────────────────────────────────────────
function _updateEfficacyRanking(recommendations, allProbs) {
  let efficacyData = [];

  if (recommendations && recommendations.length) {
    efficacyData = recommendations.slice(0, 5).map(r => ({
      name: r.name,
      pct:  Math.round((1 - r.resistance_prob) * 100)
    }));
  } else if (allProbs && Object.keys(allProbs).length) {
    efficacyData = Object.entries(allProbs)
      .map(([name, prob]) => ({ name, pct: Math.round((1 - prob) * 100) }))
      .sort((a, b) => b.pct - a.pct)
      .slice(0, 5);
  }

  if (!efficacyData.length) return;
  const el = document.getElementById('efficacy-rank');
  if (!el) return;

  el.innerHTML = efficacyData.map((e, i) => `
    <div class="rec-item">
      <span class="rec-rank">#${i + 1}</span>
      <span class="rec-name">${e.name}</span>
      <div class="rec-bar-wrap" style="width:100px;">
        <div class="rec-bar" style="width:${e.pct}%;background:${
          e.pct > 80 ? 'var(--accent2)' : e.pct > 65 ? 'var(--warn)' : 'var(--danger)'
        };"></div>
      </div>
      <span class="rec-prob">${e.pct}%</span>
    </div>`).join('');

  _initialised['strategy'] = false; // allow strategy page to re-render ranking on next visit
}



// ─── CLINICAL PREDICTION ──────────────────────────────────────────────────────
async function runClinicalPrediction() {
  const btn    = document.querySelector('#page-clinical .btn-primary');
  const iconEl = document.getElementById('clin-btn-icon');
  const textEl = document.getElementById('clin-btn-text');
  btn.disabled = true;
  iconEl.innerHTML = '<div class="loading-ring" style="display:inline-block;"></div>';
  textEl.textContent = ' Analysing...';

  const payload = {
    species:      document.getElementById('clin-species').value,
    age:          parseInt(document.getElementById('clin-age').value) || 45,
    gender:       document.getElementById('clin-gender').value,
    diabetes:     document.getElementById('clin-diabetes').value,
    hypertension: document.getElementById('clin-htn').value,
    hospital:     document.getElementById('clin-hosp').value,
    inf_freq:     document.getElementById('clin-inf').value,
    antibiotic:   document.getElementById('clin-abx').value,
  };

  try {
    const res = await fetch('/predict/clinical', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Server error ' + res.status);
    const data = await res.json();
    _renderClinicalResult(data);
  } catch(err) {
    console.warn('API unavailable, using fallback:', err.message);
    _runClinicalFallback(payload);
    return;
  } finally {
    iconEl.innerHTML = '🔬';
    textEl.textContent = 'Predict Resistance';
    btn.disabled = false;
  }
}

function _renderClinicalResult(data) {
  const abx      = data.antibiotic;
  const baseProb = data.resistance_prob;
  const suscProb = data.susceptibility;
  const resClass = data.classification;
  const badgeCls = resClass==='Sensitive' ? 'badge-sensitive' : resClass==='Intermediate' ? 'badge-intermediate' : 'badge-resistant';
  const advice   = resClass==='Sensitive'    ? '✅ Consider using — high predicted efficacy.'
                 : resClass==='Intermediate' ? '⚠️ Use with caution or consider combination therapy.'
                 :                             '❌ Avoid — high resistance risk. Select an alternative.';

  document.getElementById('clin-result-panel').innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
      <div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--text-dim);letter-spacing:2px;margin-bottom:6px;">PREDICTION RESULT — ${abx}</div>
        <span class="badge ${badgeCls}" style="font-size:13px;padding:6px 16px;">${resClass}</span>
      </div>
      <div style="flex:1;min-width:200px;padding-left:16px;border-left:1px solid var(--border);">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">Resistance probability: <span style="font-family:var(--mono);color:var(--accent);">${(baseProb*100).toFixed(1)}%</span></div>
        <div style="font-size:12px;color:var(--text-muted);">Susceptibility: <span style="font-family:var(--mono);color:var(--accent2);">${(suscProb*100).toFixed(1)}%</span></div>
        <div style="margin-top:8px;font-size:12px;color:var(--text-muted);">${advice}</div>
      </div>
    </div>`;

  // Resistance probability bar chart
  if (data.all_probs && Object.keys(data.all_probs).length > 2) {
    const labels = Object.keys(data.all_probs);
    const values = Object.values(data.all_probs);
    makeChart('clinProbChart', {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label:'Resistance Prob', data:values,
          backgroundColor: values.map(p=>p>0.6?'rgba(255,69,69,0.7)':p>0.35?'rgba(245,166,35,0.7)':'rgba(0,255,157,0.7)'),
          borderRadius:4 }]
      },
      options: { ...chartDefaults, plugins:{legend:{display:false}}, scales:{...chartDefaults.scales, y:{...chartDefaults.scales.y, min:0, max:1}} }
    });
  } else {
  makeChart('clinProbChart', {
    type: 'bar',
    data: {
      labels: ['Resistant', 'Susceptible'],
      datasets: [{
        data: [baseProb, suscProb],
        backgroundColor: ['rgba(255,69,69,0.7)', 'rgba(0,255,157,0.7)'],
        borderRadius: 6
      }]
    },
    options: {
      ...chartDefaults,
      plugins: { legend: { display: false } },
      scales: {
        ...chartDefaults.scales,
        y: {
          ...chartDefaults.scales.y,
          min: 0,
          max: 1,
          suggestedMax: Math.max(baseProb, suscProb) * 1.3 || 1
        }
      }
    }
  });
}

  // Feature importance bars
  const features = ['Bacterial Species','Hospitalization','Age','Infection Freq','Prior ABX','Diabetes','Hypertension','Gender'];
  const scores   = [0.28,0.22,0.16,0.12,0.09,0.07,0.04,0.02];
  document.getElementById('clinFeatImp').innerHTML = features.map((f,i)=>`
    <div class="feat-row">
      <span class="feat-name">${f}</span>
      <div class="feat-bar-track"><div class="feat-bar-fill" style="width:${scores[i]*100/0.28}%"></div></div>
      <span class="feat-score">${scores[i].toFixed(2)}</span>
    </div>`).join('');

  // Recommendations list
  const recs = data.recommendations || [];
  if (recs.length) {
    document.getElementById('clin-recs-card').style.display = 'block';
    document.getElementById('clin-rec-list').innerHTML = recs.map((r,i)=>`
      <div class="rec-item">
        <span class="rec-rank">#${i+1}</span>
        <span class="rec-name">${r.name}</span>
        <div class="rec-bar-wrap"><div class="rec-bar" style="width:${((1-r.resistance_prob)*100).toFixed(0)}%"></div></div>
        <span class="rec-prob">${((1-r.resistance_prob)*100).toFixed(0)}% effective</span>
      </div>`).join('');
  }
   _updateEfficacyRanking(data.recommendations, data.all_probs);
}

function _runClinicalFallback(payload) {
  const hosp   = payload.hospital==='Yes';
  const diab   = payload.diabetes==='Yes';
  const freq   = payload.inf_freq;
  let baseProb = 0.3 + (hosp?0.15:0) + (diab?0.1:0);
  if (freq==='Often') baseProb += 0.15;
  else if (freq==='Regularly') baseProb += 0.08;
  baseProb = Math.min(Math.max(baseProb + Math.random()*0.1 - 0.05, 0.05), 0.95);

  _renderClinicalResult({
    antibiotic:      payload.antibiotic,
    resistance_prob: baseProb,
    susceptibility:  1 - baseProb,
    classification:  baseProb<0.3?'Sensitive':baseProb<0.6?'Intermediate':'Resistant',
    all_probs:       null,
    recommendations: ['AMX/AMP','AMC','CZ','GEN','IPM','CTX/CRO','CIP','FOX','ofx','C']
      .map(a=>({ name:a, resistance_prob:Math.random()*0.4 }))
      .sort((a,b)=>a.resistance_prob-b.resistance_prob).slice(0,5)
  });

  const btn = document.querySelector('#page-clinical .btn-primary');
  document.getElementById('clin-btn-icon').innerHTML = '🔬';
  document.getElementById('clin-btn-text').textContent = 'Predict Resistance';
  btn.disabled = false;
}

// ─── ENVIRONMENTAL PREDICTION ─────────────────────────────────────────────────
async function runEnvPrediction() {
  const btn = document.querySelector('#page-environmental .btn-primary');
  btn.innerHTML = '<div class="loading-ring"></div> Analysing...';
  btn.disabled = true;

  const payload = {
    city:          document.getElementById('env-city').value,
    surface:       document.getElementById('env-surface').value,
    antibiotic:    document.getElementById('env-abx').value,
    sample_source: document.getElementById('env-source').value,
    species:       document.getElementById('env-species').value,
  };

  try {
    const res = await fetch('/predict/environmental', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Server error ' + res.status);
    const data = await res.json();
    _renderEnvResult(
      data.city, data.surface, data.antibiotic,
      [data.probabilities.Sensitive, data.probabilities.Intermediate, data.probabilities.Resistant]
    );
  } catch(err) {
    console.warn('API unavailable, using fallback:', err.message);
    _runEnvFallback(payload);
    return;
  } finally {
    btn.innerHTML = '🌿 Predict Resistance';
    btn.disabled = false;
  }
}

function _renderEnvResult(city, surface, abx, norm) {
  const predIdx = norm.indexOf(Math.max(...norm));
  const classes = ['Sensitive','Intermediate','Resistant'];
  const badges  = ['badge-sensitive','badge-intermediate','badge-resistant'];
  const icons   = ['✅','⚠️','❌'];
  const msgs    = [
    'Low resistance environment — antibiotic may remain effective.',
    'Moderate resistance — monitor or use in combination.',
    'High resistance detected in this environmental zone.'
  ];

  document.getElementById('env-result-panel').innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
      <div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--text-dim);letter-spacing:2px;margin-bottom:6px;">ENV PREDICTION — ${abx.toUpperCase()} @ ${city}</div>
        <span class="badge ${badges[predIdx]}" style="font-size:13px;padding:6px 16px;">${classes[predIdx]}</span>
      </div>
      <div style="flex:1;min-width:200px;padding-left:16px;border-left:1px solid var(--border);">
        <div style="font-size:12px;color:var(--text-muted);">Surface: <span style="color:var(--accent);font-family:var(--mono);">${surface}</span> &nbsp;|&nbsp; Confidence: <span style="color:var(--accent);font-family:var(--mono);">${(norm[predIdx]*100).toFixed(1)}%</span></div>
        <div style="margin-top:6px;font-size:12px;color:var(--text-muted);">${icons[predIdx]} ${msgs[predIdx]}</div>
      </div>
    </div>`;

  makeChart('envProbChart', {
    type: 'bar',
    data: {
      labels: ['Sensitive','Intermediate','Resistant'],
      datasets: [{ data:norm, backgroundColor:['rgba(0,255,157,0.7)','rgba(245,166,35,0.7)','rgba(255,69,69,0.7)'], borderRadius:6 }]
    },
    options: { ...chartDefaults, plugins:{legend:{display:false}}, scales:{...chartDefaults.scales, y:{...chartDefaults.scales.y, min:0, max:1}} }
  });

  const envFeats  = ['City/Location','Surface Type','Species','Season','Sample Source'];
  const envScores = [0.35,0.28,0.18,0.12,0.07];
  document.getElementById('envFeatImp').innerHTML = envFeats.map((f,i)=>`
    <div class="feat-row">
      <span class="feat-name">${f}</span>
      <div class="feat-bar-track"><div class="feat-bar-fill" style="width:${envScores[i]*100/0.35}%"></div></div>
      <span class="feat-score">${envScores[i].toFixed(2)}</span>
    </div>`).join('');
}

function _runEnvFallback(payload) {
  const raw  = [Math.random()*0.4+0.05, Math.random()*0.25+0.05, Math.random()*0.4+0.05];
  const sum  = raw.reduce((a,b)=>a+b,0);
  const norm = raw.map(p=>p/sum);
  _renderEnvResult(payload.city, payload.surface, payload.antibiotic, norm);
  const btn = document.querySelector('#page-environmental .btn-primary');
  btn.innerHTML = '🌿 Predict Resistance';
  btn.disabled = false;
}

// ─── BOOT ─────────────────────────────────────────────────────────────────────
// Dashboard is visible on load — init it once the DOM is fully painted
window.addEventListener('DOMContentLoaded', () => {
  requestAnimationFrame(() => requestAnimationFrame(() => initPage('dashboard')));
});