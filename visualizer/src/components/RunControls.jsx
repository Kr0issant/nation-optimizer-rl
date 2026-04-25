import { useEffect, useState } from 'react';
import clsx from 'clsx';

const DEFAULT_FORM = {
  mode: 'equal_split',
  modelId: '',
  seed: 42,
  maxRounds: 20,
  temperature: 0.2,
};

/**
 * Sidebar/header control that picks an inference mode and starts a live run.
 *
 * Props:
 *   - modes:        [{id,label,description,requires_credentials,...}]
 *   - status:       'idle' | 'connecting' | 'running' | 'done' | 'error'
 *   - lastError:    string | null
 *   - currentRunId: string | null
 *   - onStart(opts): kicks off a new run (parent handles SSE wiring)
 *   - onStop():     stops the current SSE subscription
 */
export default function RunControls({
  modes = [],
  status = 'idle',
  lastError = null,
  currentRunId = null,
  onStart,
  onStop,
}) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [open, setOpen] = useState(true);

  // Make sure the selected mode stays valid when the modes list refreshes.
  useEffect(() => {
    if (!modes.length) return;
    if (!modes.find(m => m.id === form.mode)) {
      setForm(f => ({ ...f, mode: modes[0].id }));
    }
  }, [modes, form.mode]);

  const selectedMode = modes.find(m => m.id === form.mode);
  const llmReady = selectedMode?.id !== 'llm' || selectedMode?.credentials_present;

  function update(key, value) {
    setForm(f => ({ ...f, [key]: value }));
  }

  function submit(e) {
    e.preventDefault();
    onStart?.({
      mode: form.mode,
      modelId: form.modelId || selectedMode?.default_model_id || null,
      seed: Number(form.seed) || 0,
      maxRounds: Number(form.maxRounds) || 20,
      temperature: Number(form.temperature) || 0,
    });
  }

  const isBusy = status === 'connecting' || status === 'running';

  return (
    <div className="run-controls card">
      <h3>
        Live inference
        <span className="meta">
          {currentRunId ? <code>{currentRunId}</code> : 'no run yet'}
        </span>
      </h3>

      <button
        type="button"
        className="run-controls__toggle"
        onClick={() => setOpen(o => !o)}
      >
        {open ? 'Hide controls' : 'Show controls'}
      </button>

      {open && (
        <form className="run-controls__form" onSubmit={submit}>
          <label className="run-controls__field">
            <span>Policy</span>
            <select
              value={form.mode}
              onChange={e => update('mode', e.target.value)}
              disabled={isBusy}
            >
              {modes.map(m => (
                <option key={m.id} value={m.id}>
                  {m.label}
                  {m.requires_credentials && !m.credentials_present
                    ? ' (no token)'
                    : ''}
                </option>
              ))}
            </select>
            {selectedMode?.description && (
              <small className="run-controls__hint">
                {selectedMode.description}
              </small>
            )}
          </label>

          {selectedMode?.id === 'llm' && (
            <label className="run-controls__field">
              <span>Model id</span>
              <input
                type="text"
                value={form.modelId}
                onChange={e => update('modelId', e.target.value)}
                placeholder={
                  selectedMode.default_model_id || 'mistralai/Mistral-7B-Instruct-v0.3'
                }
                disabled={isBusy}
              />
            </label>
          )}

          <div className="run-controls__row">
            <label className="run-controls__field">
              <span>Seed</span>
              <input
                type="number"
                min={0}
                value={form.seed}
                onChange={e => update('seed', e.target.value)}
                disabled={isBusy}
              />
            </label>
            <label className="run-controls__field">
              <span>Max rounds</span>
              <input
                type="number"
                min={1}
                max={50}
                value={form.maxRounds}
                onChange={e => update('maxRounds', e.target.value)}
                disabled={isBusy}
              />
            </label>
            {selectedMode?.id === 'llm' && (
              <label className="run-controls__field">
                <span>Temp</span>
                <input
                  type="number"
                  step="0.1"
                  min={0}
                  max={2}
                  value={form.temperature}
                  onChange={e => update('temperature', e.target.value)}
                  disabled={isBusy}
                />
              </label>
            )}
          </div>

          <div className="run-controls__actions">
            <button
              type="submit"
              className="primary"
              disabled={isBusy || !llmReady}
              title={
                !llmReady
                  ? 'Set HF_TOKEN and HF_MODEL_ID in the server .env first'
                  : undefined
              }
            >
              {status === 'connecting' && 'Starting…'}
              {status === 'running' && 'Running…'}
              {(status === 'idle' || status === 'done' || status === 'error') &&
                'Start run'}
            </button>
            {isBusy && (
              <button type="button" onClick={() => onStop?.()}>
                Stop stream
              </button>
            )}
          </div>

          <div
            className={clsx('run-controls__status', `is-${status}`)}
            role="status"
          >
            <span className="dot" />
            {statusLabel(status)}
            {lastError && (
              <em className="run-controls__error">{lastError}</em>
            )}
          </div>

          {selectedMode?.id === 'llm' && !selectedMode?.credentials_present && (
            <small className="run-controls__warn">
              The server is missing <code>HF_TOKEN</code> /{' '}
              <code>HF_MODEL_ID</code>. Set them in <code>.env</code> and
              restart <code>scripts/run_visualizer_server.py</code>.
            </small>
          )}
        </form>
      )}
    </div>
  );
}

function statusLabel(status) {
  switch (status) {
    case 'connecting':
      return 'Connecting to backend…';
    case 'running':
      return 'Streaming live rounds';
    case 'done':
      return 'Run complete';
    case 'error':
      return 'Run failed';
    default:
      return 'Idle';
  }
}
