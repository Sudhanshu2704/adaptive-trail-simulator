import { useState } from 'react';

const DEFAULT_ARMS = [
  { name: 'Control', effect_size: 0.0, locked: true },
  { name: 'Arm_A', effect_size: 0.5, locked: false },
  { name: 'Arm_B', effect_size: 1.2, locked: false },
];

export default function TrialConfigForm({ onSubmit, loading }) {
  const [arms, setArms] = useState(DEFAULT_ARMS);
  const [patientsPerArm, setPatientsPerArm] = useState(50);
  const [maxPhases, setMaxPhases] = useState(5);
  const [threshold, setThreshold] = useState(0.95);

  const addArm = () => {
    if (arms.length >= 6) return;
    setArms([...arms, { name: `Arm_${String.fromCharCode(65 + arms.length - 1)}`, effect_size: 0.5, locked: false }]);
  };

  const removeArm = (idx) => {
    if (arms[idx].locked) return;
    setArms(arms.filter((_, i) => i !== idx));
  };

  const updateArm = (idx, field, value) => {
    const updated = arms.map((arm, i) =>
      i === idx ? { ...arm, [field]: field === 'effect_size' ? parseFloat(value) : value } : arm
    );
    setArms(updated);
  };

  const handleSubmit = () => {
    onSubmit({
      arms: arms.map(({ name, effect_size }) => ({ name, effect_size })),
      patients_per_arm: patientsPerArm,
      max_phases: maxPhases,
      stopping_threshold: threshold,
    });
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Trial Configuration</h2>
          <p className="text-xs text-slate-400 mt-0.5">Configure arms, effect sizes, and stopping rules</p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Arms Builder */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-slate-300">Trial Arms</label>
            <button
              onClick={addArm}
              disabled={arms.length >= 6}
              className="text-xs px-2 py-1 rounded bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-700/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              + Add Arm
            </button>
          </div>

          <div className="space-y-2">
            {arms.map((arm, idx) => (
              <div key={idx} className="flex items-center gap-3 bg-slate-900/50 rounded-lg p-3 border border-slate-700/60">
                <div className="flex-1 min-w-0">
                  <input
                    type="text"
                    value={arm.name}
                    onChange={(e) => updateArm(idx, 'name', e.target.value)}
                    disabled={arm.locked}
                    className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none disabled:text-slate-400"
                    placeholder="Arm name"
                  />
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-slate-500">Effect</span>
                  <input
                    type="number"
                    value={arm.effect_size}
                    onChange={(e) => updateArm(idx, 'effect_size', e.target.value)}
                    disabled={arm.locked}
                    step="0.1"
                    min="0"
                    max="5"
                    className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white text-center focus:outline-none focus:border-blue-500 disabled:opacity-50"
                  />
                </div>

                {arm.locked ? (
                  <span className="text-xs text-slate-600 w-12 text-center">Control</span>
                ) : (
                  <button
                    onClick={() => removeArm(idx)}
                    className="text-slate-600 hover:text-red-400 transition-colors text-sm w-12 text-center"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-2">Effect size is relative to Control (0.0). Higher = stronger treatment signal.</p>
        </div>

        {/* Numeric Parameters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Patients / Arm</label>
            <input
              type="number"
              value={patientsPerArm}
              onChange={(e) => setPatientsPerArm(parseInt(e.target.value))}
              min={20}
              max={200}
              step={10}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-600 mt-1">20 – 200</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Max Phases</label>
            <input
              type="number"
              value={maxPhases}
              onChange={(e) => setMaxPhases(parseInt(e.target.value))}
              min={2}
              max={10}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-600 mt-1">2 – 10</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Success Threshold</label>
            <div className="relative">
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                min={0.8}
                max={0.999}
                step={0.01}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <p className="text-xs text-slate-600 mt-1">P(treatment &gt; control)</p>
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading || arms.length < 2}
          className={`w-full py-3 rounded-lg font-semibold text-white transition-all ${
            loading
              ? 'bg-blue-800/40 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 shadow-lg hover:shadow-blue-500/25 active:scale-[0.99]'
          }`}
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Running Simulation…
            </span>
          ) : 'Run Simulation'}
        </button>
      </div>
    </div>
  );
}
