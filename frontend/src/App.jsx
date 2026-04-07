import { useState } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// Spinner SVG Component
const Spinner = () => (
  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

export default function App() {
  const [loading, setLoading] = useState(false);
  const [trialResults, setTrialResults] = useState(null);
  const [errorModal, setErrorModal] = useState(null);

  const runSimulation = async () => {
    setLoading(true);
    setErrorModal(null);
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/v1/simulate-trial', {
        arms: ["Control", "Arm_A", "Arm_B"],
        patients_per_arm: 50
      });
      setTrialResults(response.data);
    } catch (error) {
      setErrorModal("Failed to connect to the backend. Is your Python server running?");
    } finally {
      setLoading(false);
    }
  };

  // Phase 1: Data Transformation
  const getChartData = () => {
    if (!trialResults || !trialResults.history) return [];
    
    // Filter stats
    const statsHistory = trialResults.history.filter(item => item.type === "stats");
    
    return statsHistory.map(item => {
      const phaseData = { phase: `Phase ${item.phase}` };
      // item.data format: { "Arm_A": { "mean_difference": ... }, "Arm_B": ... }
      for (const [armName, stats] of Object.entries(item.data)) {
        phaseData[armName] = stats.mean_difference;
      }
      return phaseData;
    });
  };

  const getTimelineActions = () => {
    if (!trialResults || !trialResults.history) return [];
    return trialResults.history.filter(item => item.type === "action");
  };

  const chartData = getChartData();
  const timelineActions = getTimelineActions();

  // Color mapping logic for recharts
  const armColors = {
    "Arm_A": "#10b981", // Emerald 500
    "Arm_B": "#3b82f6", // Blue 500
    "Control": "#64748b" // Slate 500
  };

  return (
    <div className="min-h-screen bg-slate-900 p-8 text-white relative">
      {/* Error Modal Overlay */}
      {errorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-red-500 rounded-lg shadow-xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-red-400 mb-2">Simulation Error</h3>
            <p className="text-slate-300 mb-6">{errorModal}</p>
            <button 
              onClick={() => setErrorModal(null)}
              className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded transition-colors w-full"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header Section */}
        <header className="border-b border-slate-700 pb-4">
          <h1 className="text-3xl font-bold text-white mb-2">AI Adaptive Trial Simulator</h1>
          <p className="text-slate-400">Powered by LangGraph, FastAPI, Recharts, and Local LLMs</p>
        </header>

        {/* Control Panel */}
        <div className="bg-slate-800 p-6 rounded-lg shadow-lg border border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Trial Configuration</h2>
            <p className="text-sm text-slate-400">3 Arms (Control, Arm_A, Arm_B) • 50 Patients/Phase</p>
          </div>
          
          <button 
            onClick={runSimulation}
            disabled={loading}
            className={`px-6 py-3 rounded-md font-bold text-white transition-all whitespace-nowrap ${
              loading 
                ? 'bg-blue-800/50 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-500 shadow-md hover:shadow-blue-500/20'
            }`}
          >
            {loading ? <><Spinner /> Simulating...</> : 'Start Trial'}
          </button>
        </div>

        {/* Results Section */}
        {trialResults && (
          <div className="space-y-6">
            
            {/* Visualizer Card */}
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
              <h2 className="text-xl font-semibold mb-6">Mean Difference Over Phases</h2>
              <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%" minHeight={400} minWidth={1}>
                  <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="phase" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" label={{ value: 'Mean Diff.', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                      itemStyle={{ color: '#e2e8f0' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }}/>
                    
                    {/* Render Lines Dynamically based on Data Keys */}
                    {chartData.length > 0 && Object.keys(chartData[0])
                      .filter(key => key !== 'phase')
                      .map((armKey) => (
                        <Line 
                          key={armKey}
                          type="monotone" 
                          dataKey={armKey} 
                          stroke={armColors[armKey] || "#a855f7"} 
                          strokeWidth={3}
                          activeDot={{ r: 8 }} 
                        />
                      ))
                    }
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Event Timeline */}
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
              <h2 className="text-xl font-semibold mb-6">AI Agent Timeline</h2>
              
              {timelineActions.length === 0 ? (
                <p className="text-slate-400 italic">No significant AI actions recorded yet.</p>
              ) : (
                <div className="space-y-4 border-l-2 border-slate-600 ml-4 pl-4 relative">
                  {timelineActions.map((action, idx) => (
                    <div key={idx} className="relative">
                      {/* Timeline dot */}
                      <span className="absolute -left-[25px] flex items-center justify-center w-6 h-6 bg-slate-900 rounded-full border-2 border-slate-600">
                        <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                      </span>
                      
                      <div className="bg-slate-900/50 rounded p-4 border border-slate-700/50 hover:border-slate-600 transition-colors">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-sm font-semibold text-slate-400 bg-slate-800 px-2 py-1 rounded">
                            Phase {action.phase}
                          </span>
                          
                          {/* Badges based on action type */}
                          {action.decision === 'STOP_ARM_FUTILITY' && (
                            <span className="text-xs font-bold text-red-200 bg-red-900/60 border border-red-700/50 px-2 py-1 rounded-full flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-red-500"></span>
                              Dropped {action.target} (Futility)
                            </span>
                          )}
                          
                          {action.decision === 'STOP_TRIAL_SUCCESS' && (
                            <span className="text-xs font-bold text-green-200 bg-green-900/60 border border-green-700/50 px-2 py-1 rounded-full flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-green-500"></span>
                              Trial Success ({action.target})
                            </span>
                          )}

                          {action.decision === 'CONTINUE' && (
                            <span className="text-xs font-bold text-blue-200 bg-blue-900/60 border border-blue-700/50 px-2 py-1 rounded-full flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                              Continue Trial
                            </span>
                          )}
                        </div>
                        
                        <p className="text-slate-300 text-sm mt-2 leading-relaxed">
                          <span className="font-semibold text-slate-400">Agent Reasoning:</span> {action.reasoning || "No reasoning provided."}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        )}

      </div>
    </div>
  );
}