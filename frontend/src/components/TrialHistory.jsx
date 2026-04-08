import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const STATUS_COLORS = {
  completed: 'text-green-400 bg-green-900/30 border-green-700/50',
  stopped_early: 'text-yellow-400 bg-yellow-900/30 border-yellow-700/50',
};

function formatDate(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function TrialHistory({ onViewTrial }) {
  const [trials, setTrials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchTrials();
  }, []);

  const fetchTrials = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_URL}/api/v1/trials`);
      setTrials(res.data);
    } catch {
      setError('Could not load trial history. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const viewDetail = async (id) => {
    if (selectedId === id) {
      setSelectedId(null);
      setDetail(null);
      return;
    }
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/v1/trials/${id}`);
      setDetail(res.data);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-400 gap-2">
        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Loading history…
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700/50 rounded-xl p-6 text-red-300 text-sm">{error}</div>
    );
  }

  if (trials.length === 0) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-10 text-center text-slate-400">
        <p className="text-2xl mb-2">📋</p>
        <p className="font-medium">No trials yet</p>
        <p className="text-sm mt-1">Run your first simulation on the "Run Trial" tab.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Past Simulations</h2>
        <button onClick={fetchTrials} className="text-xs text-slate-400 hover:text-white transition-colors">↻ Refresh</button>
      </div>

      {trials.map((trial) => (
        <div key={trial.id} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          {/* Row */}
          <button
            onClick={() => viewDetail(trial.id)}
            className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-slate-700/40 transition-colors"
          >
            <span className="text-slate-500 text-sm font-mono w-10">#{trial.id}</span>

            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium truncate">
                {trial.initial_arms?.join(' · ') || '—'}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{formatDate(trial.created_at)}</p>
            </div>

            <span className={`text-xs font-semibold px-2 py-1 rounded-full border shrink-0 ${STATUS_COLORS[trial.status] || 'text-slate-400 bg-slate-700 border-slate-600'}`}>
              {trial.status === 'completed' ? '✓ Success' : '⚠ Stopped Early'}
            </span>

            <span className="text-xs text-slate-500 shrink-0">Phase {trial.final_phase}</span>

            <span className="text-slate-600 shrink-0">{selectedId === trial.id ? '▲' : '▼'}</span>
          </button>

          {/* Detail Accordion */}
          {selectedId === trial.id && (
            <div className="border-t border-slate-700 px-5 py-4 bg-slate-900/40">
              {detailLoading ? (
                <p className="text-slate-400 text-sm">Loading…</p>
              ) : detail ? (
                <div className="space-y-3">
                  {detail.history
                    .filter((h) => h.type === 'action')
                    .map((action, idx) => (
                      <div key={idx} className="text-sm border-l-2 border-slate-600 pl-3">
                        <span className="text-slate-400 font-medium">Phase {action.phase}</span>
                        {' · '}
                        <span className={
                          action.decision === 'STOP_TRIAL_SUCCESS' ? 'text-green-400' :
                          action.decision === 'STOP_ARM_FUTILITY' ? 'text-red-400' :
                          'text-blue-400'
                        }>
                          {action.decision}
                        </span>
                        {action.target && action.target !== 'All' && (
                          <span className="text-slate-500"> → {action.target}</span>
                        )}
                        <p className="text-slate-500 text-xs mt-1 leading-relaxed">{action.reasoning}</p>
                      </div>
                    ))
                  }
                  {onViewTrial && (
                    <button
                      onClick={() => onViewTrial(detail)}
                      className="mt-2 text-xs px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-700/50 transition-colors"
                    >
                      View Full Charts →
                    </button>
                  )}
                </div>
              ) : (
                <p className="text-slate-500 text-sm">Could not load details.</p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
