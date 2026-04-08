import { useState } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import TrialConfigForm from './components/TrialConfigForm';
import TrialHistory from './components/TrialHistory';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Deterministic color palette for up to 6 arms
const ARM_COLORS = ['#64748b', '#10b981', '#3b82f6', '#f59e0b', '#a855f7', '#ef4444'];

function getArmColor(armName, armList) {
  const idx = armList.indexOf(armName);
  return ARM_COLORS[idx % ARM_COLORS.length] || '#94a3b8';
}

// --- CSV Export Utility ---
function exportToCSV(trialResults) {
  if (!trialResults?.history) return;
  const statsRows = trialResults.history
    .filter((h) => h.type === 'stats')
    .flatMap((h) =>
      Object.entries(h.data).map(([arm, stats]) => ({
        phase: h.phase,
        arm,
        control_mean: stats.control_mean ?? '',
        treatment_mean: stats.treatment_mean ?? '',
        mean_difference: stats.mean_difference ?? '',
        prob_superior: stats.t_statistic ?? '',
        p_value: stats.p_value ?? '',
        is_significant: stats.is_significant_05 ?? '',
        is_futile: stats.is_failing_futility ?? '',
      }))
    );

  const headers = Object.keys(statsRows[0] || {}).join(',');
  const rows = statsRows.map((r) => Object.values(r).join(',')).join('\n');
  const blob = new Blob([`${headers}\n${rows}`], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `trial_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// --- Chart Data Transformer ---
function getChartData(trialResults) {
  if (!trialResults?.history) return [];
  return trialResults.history
    .filter((h) => h.type === 'stats')
    .map((h) => {
      const row = { phase: `Phase ${h.phase}` };
      for (const [arm, stats] of Object.entries(h.data)) {
        row[arm] = stats.mean_difference;
      }
      return row;
    });
}

function getTimelineActions(trialResults) {
  if (!trialResults?.history) return [];
  return trialResults.history.filter((h) => h.type === 'action');
}

// --- Sub-components ---
function TabButton({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2 text-sm font-medium rounded-lg transition-all ${
        active
          ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
          : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
      }`}
    >
      {label}
    </button>
  );
}

function ResultsPanel({ trialResults, allArmNames }) {
  const chartData = getChartData(trialResults);
  const timelineActions = getTimelineActions(trialResults);

  return (
    <div className="space-y-6 animate-fade-in">

      {/* Summary Banner */}
      <div className={`rounded-xl p-4 border flex items-center justify-between gap-4 ${
        trialResults.status === 'success'
          ? 'bg-green-900/20 border-green-700/50'
          : 'bg-yellow-900/20 border-yellow-700/50'
      }`}>
        <div>
          <p className={`font-semibold ${trialResults.status === 'success' ? 'text-green-300' : 'text-yellow-300'}`}>
            {trialResults.status === 'success' ? '✓ Trial Completed Successfully' : '⚠ Trial Stopped (Max Phases)'}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {trialResults.final_phase} phase{trialResults.final_phase !== 1 ? 's' : ''} completed ·
            Arms remaining: {trialResults.active_arms_remaining?.join(', ') || '—'}
            {trialResults.trial_id && ` · Trial #${trialResults.trial_id}`}
          </p>
        </div>
        <button
          onClick={() => exportToCSV(trialResults)}
          className="shrink-0 text-xs px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 border border-slate-600 transition-colors"
        >
          ↓ Export CSV
        </button>
      </div>

      {/* Line Chart */}
      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
        <h2 className="text-base font-semibold text-white mb-5">Mean Difference Over Phases</h2>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="phase" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }}
                label={{ value: 'Mean Diff.', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc', fontSize: 12 }}
                itemStyle={{ color: '#e2e8f0' }}
              />
              <Legend wrapperStyle={{ paddingTop: '16px', fontSize: 12 }} />
              {chartData.length > 0 &&
                Object.keys(chartData[0])
                  .filter((k) => k !== 'phase')
                  .map((armKey) => (
                    <Line
                      key={armKey}
                      type="monotone"
                      dataKey={armKey}
                      stroke={getArmColor(armKey, allArmNames)}
                      strokeWidth={2.5}
                      dot={{ r: 4 }}
                      activeDot={{ r: 7 }}
                    />
                  ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent Timeline */}
      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
        <h2 className="text-base font-semibold text-white mb-5">AI Agent Decision Timeline</h2>
        {timelineActions.length === 0 ? (
          <p className="text-slate-500 text-sm italic">No AI decisions recorded.</p>
        ) : (
          <div className="space-y-3 border-l-2 border-slate-700 ml-2 pl-4">
            {timelineActions.map((action, idx) => (
              <div key={idx} className="relative">
                <span className="absolute -left-[21px] w-5 h-5 flex items-center justify-center bg-slate-900 rounded-full border-2 border-slate-600">
                  <span className={`w-2 h-2 rounded-full ${
                    action.decision === 'STOP_TRIAL_SUCCESS' ? 'bg-green-500' :
                    action.decision === 'STOP_ARM_FUTILITY' ? 'bg-red-500' : 'bg-blue-500'
                  }`} />
                </span>
                <div className="bg-slate-900/60 rounded-lg p-3.5 border border-slate-700/60 hover:border-slate-600 transition-colors">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-xs text-slate-400 bg-slate-800 px-2 py-0.5 rounded font-medium">Phase {action.phase}</span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                      action.decision === 'STOP_TRIAL_SUCCESS' ? 'text-green-300 bg-green-900/50 border-green-700/50' :
                      action.decision === 'STOP_ARM_FUTILITY' ? 'text-red-300 bg-red-900/50 border-red-700/50' :
                      'text-blue-300 bg-blue-900/50 border-blue-700/50'
                    }`}>
                      {action.decision.replace(/_/g, ' ')}
                      {action.target && action.target !== 'All' ? ` → ${action.target}` : ''}
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">{action.reasoning || 'No reasoning provided.'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// --- Main App ---
export default function App() {
  const [activeTab, setActiveTab] = useState('run');
  const [loading, setLoading] = useState(false);
  const [trialResults, setTrialResults] = useState(null);
  const [allArmNames, setAllArmNames] = useState([]);
  const [errorModal, setErrorModal] = useState(null);

  const runSimulation = async (config) => {
    setLoading(true);
    setErrorModal(null);
    setTrialResults(null);
    setAllArmNames(config.arms.map((a) => a.name));
    try {
      const response = await axios.post(`${API_URL}/api/v1/simulate-trial`, config);
      setTrialResults(response.data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setErrorModal(detail || 'Failed to connect to the backend. Is the server running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Error Modal */}
      {errorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-red-600/60 rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-red-400 mb-2">Simulation Error</h3>
            <p className="text-slate-300 text-sm mb-5 leading-relaxed">{errorModal}</p>
            <button
              onClick={() => setErrorModal(null)}
              className="w-full py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">

        {/* Header */}
        <header className="border-b border-slate-700/60 pb-5">
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Adaptive Trial Simulator</h1>
          <p className="text-slate-400 text-sm mt-1">
            Bayesian adaptive randomization · LangGraph agent · NumPyro MCMC
          </p>
        </header>

        {/* Tab Bar */}
        <div className="flex gap-2 bg-slate-800/50 rounded-xl p-1 border border-slate-700/50 w-fit">
          <TabButton label="Run Trial" active={activeTab === 'run'} onClick={() => setActiveTab('run')} />
          <TabButton label="History" active={activeTab === 'history'} onClick={() => setActiveTab('history')} />
        </div>

        {/* Tab Content */}
        {activeTab === 'run' && (
          <div className="space-y-6">
            <TrialConfigForm onSubmit={runSimulation} loading={loading} />
            {trialResults && (
              <ResultsPanel trialResults={trialResults} allArmNames={allArmNames} />
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <TrialHistory
            onViewTrial={(detail) => {
              setAllArmNames(detail.initial_arms || []);
              setTrialResults({ ...detail, status: detail.status === 'completed' ? 'success' : 'stopped' });
              setActiveTab('run');
            }}
          />
        )}

      </div>
    </div>
  );
}