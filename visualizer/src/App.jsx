import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import './App.css';
import { normalizeEpisode } from './utils/normalizeEpisode.js';
import {
  getConfig,
  getModes,
  getSnapshot,
  startRun,
  streamRun,
} from './utils/api.js';
import RoundOverview from './components/RoundOverview.jsx';
import SectorCard from './components/SectorCard.jsx';
import PhasePanel from './components/PhasePanel.jsx';
import RewardCard from './components/RewardCard.jsx';
import TimeSeries from './components/TimeSeries.jsx';
import RunControls from './components/RunControls.jsx';

const SPEEDS = [0.5, 1, 2, 4, 8];

const EMPTY_EPISODE_BASE = {
  episode_id: '',
  policy: '',
  seed: null,
  rounds: [],
  summary: null,
};

function termPillClass(reason) {
  if (!reason) return 'neutral';
  if (reason.includes('PROSPERITY')) return 'success';
  if (reason.includes('MAX_ROUNDS')) return 'neutral';
  return 'failure';
}

function makeEmptyEpisode(config) {
  return normalizeEpisode({ ...EMPTY_EPISODE_BASE, config: config || { sectors: [] } });
}

export default function App() {
  const [serverConfig, setServerConfig] = useState(null);
  const [modes, setModes] = useState([]);
  const [bootstrapError, setBootstrapError] = useState(null);

  const [episode, setEpisode] = useState(null);
  const [runId, setRunId] = useState(null);
  const [runMeta, setRunMeta] = useState(null); // {policy, mode, seed, max_rounds}
  const [status, setStatus] = useState('idle'); // idle | connecting | running | done | error
  const [lastError, setLastError] = useState(null);

  const [roundIdx, setRoundIdx] = useState(0);
  const [follow, setFollow] = useState(true); // jump to newest round automatically
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [liveRound, setLiveRound] = useState(null); // partial round being built
  const fileInputRef = useRef(null);

  const streamRef = useRef(null);
  const pendingRoundsRef = useRef([]);
  const liveRoundRef = useRef(null); // mirror for callbacks

  // ── Bootstrap: backend config + mode list ─────────────────────────────
  useEffect(() => {
    let alive = true;
    Promise.all([getConfig(), getModes()])
      .then(([cfg, modesResp]) => {
        if (!alive) return;
        setServerConfig(cfg);
        setModes(modesResp.modes || []);
        setEpisode(prev => prev || makeEmptyEpisode(cfg));
      })
      .catch(err => {
        if (!alive) return;
        setBootstrapError(err.message || String(err));
      });
    return () => {
      alive = false;
    };
  }, []);

  // ── Episode helpers ───────────────────────────────────────────────────
  const rounds = episode?.rounds || [];
  const hasRounds = rounds.length > 0;
  const currentSafeIdx = hasRounds ? Math.min(roundIdx, rounds.length - 1) : 0;
  const current = hasRounds ? rounds[currentSafeIdx] : null;
  const prev = currentSafeIdx > 0 ? rounds[currentSafeIdx - 1] : null;

  const sectorMap = useMemo(() => {
    const list = episode?.config?.sectors || [];
    return Object.fromEntries(list.map(s => [s.name, s]));
  }, [episode]);

  // When following live and viewing the latest position, show the in-progress
  // round's partial data (debate, proposals, votes streaming in). Once the
  // full round record arrives, `liveRound` is cleared and the completed
  // round takes over.
  const isViewingLatest =
    follow && hasRounds ? currentSafeIdx === rounds.length - 1 : !hasRounds;
  const showLiveRound = isViewingLatest && liveRound && status === 'running';

  // The "display round" for the PhasePanel: use partial live data when
  // streaming and the user is at the latest position; otherwise the
  // completed round record.
  const phasePanelRound = showLiveRound ? liveRound : current;

  // ── Auto-follow newest round when streaming ──────────────────────────
  useEffect(() => {
    if (!follow || !hasRounds) return;
    setRoundIdx(rounds.length - 1);
  }, [rounds.length, follow, hasRounds]);

  // ── Manual playback (for completed runs) ──────────────────────────────
  useEffect(() => {
    if (!playing || !hasRounds) return undefined;
    if (status === 'running') {
      // Streaming auto-advances on its own.
      return undefined;
    }
    const interval = 1100 / speed;
    const id = setInterval(() => {
      setRoundIdx(idx => {
        if (idx >= rounds.length - 1) {
          setPlaying(false);
          return idx;
        }
        return idx + 1;
      });
    }, interval);
    return () => clearInterval(id);
  }, [playing, speed, rounds.length, hasRounds, status]);

  // ── Apply newly-streamed rounds via normalization ─────────────────────
  const refreshFromRawRounds = useCallback(
    (rawRoundsList, summary, meta) => {
      if (!serverConfig) return;
      const next = normalizeEpisode({
        episode_id: meta?.run_id || episode?.episode_id || '',
        seed: meta?.seed ?? episode?.seed,
        policy: meta?.policy || episode?.policy || '',
        config: serverConfig,
        rounds: rawRoundsList,
        summary: summary ?? null,
      });
      setEpisode(next);
    },
    [serverConfig, episode],
  );

  // Flush any rounds that arrived while we were waiting for setState batches.
  const flushPending = useCallback(() => {
    if (pendingRoundsRef.current.length === 0) return;
    const all = pendingRoundsRef.current.slice();
    refreshFromRawRounds(all, null, runMeta);
  }, [refreshFromRawRounds, runMeta]);

  // ── SSE integration ───────────────────────────────────────────────────
  const teardownStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.close();
      streamRef.current = null;
    }
  }, []);

  const handleStart = useCallback(
    async opts => {
      try {
        setStatus('connecting');
        setLastError(null);
        teardownStream();
        pendingRoundsRef.current = [];
        const resp = await startRun(opts);
        setRunId(resp.run_id);
        setRunMeta({
          run_id: resp.run_id,
          policy: resp.policy,
          mode: resp.mode,
          seed: resp.seed,
          max_rounds: resp.max_rounds,
        });
        setEpisode(
          normalizeEpisode({
            episode_id: resp.run_id,
            seed: resp.seed,
            policy: resp.policy,
            config: resp.config || serverConfig,
            rounds: [],
            summary: null,
          }),
        );
        setRoundIdx(0);
        setFollow(true);
        setPlaying(false);

        const meta = {
          run_id: resp.run_id,
          seed: resp.seed,
          policy: resp.policy,
          mode: resp.mode,
        };

        const stream = streamRun(resp.run_id, {
          onStart: () => setStatus('running'),
          onActivity: data => {
            if (data.kind === 'round_start') {
              const partial = {
                round_num: data.round_num,
                year: Math.floor((data.round_num - 1) / 4) + 1,
                quarter: ((data.round_num - 1) % 4) + 1,
                events: data.events || [],
                crisis_occurred: data.crisis_occurred || false,
                treasury_before: data.treasury_before ?? 0,
                debate: [],
                proposals: [],
                votes: [],
                vote_results: [],
                proposal_order: [],
                _phase: 'events',
              };
              liveRoundRef.current = partial;
              setLiveRound({ ...partial });
            } else if (data.kind === 'debate') {
              const lr = liveRoundRef.current;
              if (lr) {
                lr.debate.push({
                  agent_id: data.agent_id,
                  department: data.department,
                  message: data.message,
                });
                lr._phase = 'debate';
                setLiveRound({ ...lr, debate: [...lr.debate] });
              }
            } else if (data.kind === 'proposal') {
              const lr = liveRoundRef.current;
              if (lr) {
                lr.proposals.push(data);
                lr._phase = 'proposals';
                setLiveRound({ ...lr, proposals: [...lr.proposals] });
              }
            } else if (data.kind === 'vote') {
              const lr = liveRoundRef.current;
              if (lr) {
                lr.votes.push(data);
                lr._phase = 'votes';
                setLiveRound({ ...lr, votes: [...lr.votes] });
              }
            }
          },
          onRound: roundData => {
            liveRoundRef.current = null;
            setLiveRound(null);
            pendingRoundsRef.current.push(roundData);
            refreshFromRawRounds(
              pendingRoundsRef.current.slice(),
              null,
              meta,
            );
          },
          onSummary: summaryData => {
            refreshFromRawRounds(
              pendingRoundsRef.current.slice(),
              summaryData,
              meta,
            );
          },
          onError: errData => {
            setLastError(errData.message || 'Unknown error');
            setStatus('error');
          },
          onDone: () => {
            liveRoundRef.current = null;
            setLiveRound(null);
            setStatus(s => (s === 'error' ? 'error' : 'done'));
          },
          onConnectionError: () => {
            setStatus(s =>
              s === 'done' || s === 'error' ? s : 'error',
            );
          },
        });
        streamRef.current = stream;
      } catch (err) {
        setLastError(err.message || String(err));
        setStatus('error');
      }
    },
    [refreshFromRawRounds, serverConfig, teardownStream],
  );

  const handleStop = useCallback(() => {
    teardownStream();
    setStatus(s => (s === 'running' || s === 'connecting' ? 'done' : s));
  }, [teardownStream]);

  // ── On reload while a run was active, fetch its snapshot. ─────────────
  useEffect(() => {
    if (!runId || streamRef.current) return undefined;
    let alive = true;
    getSnapshot(runId)
      .then(snap => {
        if (!alive) return;
        setEpisode(normalizeEpisode(snap));
        setRunMeta({
          run_id: snap.episode_id || runId,
          seed: snap.seed,
          policy: snap.policy,
          mode: snap.mode,
          max_rounds: snap.max_rounds,
        });
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [runId]);

  useEffect(() => {
    return () => teardownStream();
  }, [teardownStream]);

  // ── File loading (offline episodes still supported) ───────────────────
  function onLoadFile(file) {
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const parsed = JSON.parse(e.target.result);
        if (!parsed.rounds || !Array.isArray(parsed.rounds)) {
          alert('Invalid episode file: missing "rounds" array');
          return;
        }
        if (!parsed.config?.sectors) {
          alert('Invalid episode file: missing "config.sectors"');
          return;
        }
        teardownStream();
        setStatus('idle');
        setRunId(null);
        setRunMeta(null);
        setEpisode(normalizeEpisode(parsed));
        setRoundIdx(0);
        setFollow(false);
      } catch (err) {
        alert(`Failed to parse episode JSON: ${err.message}`);
      }
    };
    reader.readAsText(file);
  }

  function onDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) onLoadFile(file);
  }

  // ── Render ────────────────────────────────────────────────────────────
  if (bootstrapError) {
    return (
      <div className="app">
        <header className="topbar">
          <div className="brand">
            <span className="dot" />
            <span>Parliament RL · Episode Viewer</span>
          </div>
        </header>
        <div className="dropzone" style={{ marginTop: 32 }}>
          <strong>Backend unreachable.</strong>
          <div style={{ marginTop: 8 }}>{bootstrapError}</div>
          <div style={{ marginTop: 8, fontFamily: 'var(--mono)' }}>
            Start the streaming server with:
            <br />
            <span className="kbd">python -m scripts.run_visualizer_server</span>
          </div>
        </div>
      </div>
    );
  }

  const showShell = !!episode;

  return (
    <div className="app" onDragOver={e => e.preventDefault()} onDrop={onDrop}>
      <header className="topbar">
        <div className="brand">
          <span className="dot" />
          <span>Parliament RL · Episode Viewer</span>
        </div>
        <div className="episode-meta">
          <span>policy <b>{episode?.policy || '—'}</b></span>
          <span>mode <b>{runMeta?.mode || '—'}</b></span>
          <span>seed <b>{episode?.seed ?? '—'}</b></span>
          <span>id <b>{episode?.episode_id || '—'}</b></span>
          <span>rounds <b>{rounds.length}</b></span>
        </div>
        <div className="spacer" />
        <div className="actions">
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Load an episode JSON exported by evaluation/export_episode.py"
          >
            Load episode JSON
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json"
            style={{ display: 'none' }}
            onChange={e => e.target.files?.[0] && onLoadFile(e.target.files[0])}
          />
        </div>
      </header>

      <div className="playback">
        <div className="round-label">
          {hasRounds ? (
            <>
              Round <b style={{ color: 'var(--text-hi)' }}>{current.round_num}</b> /{' '}
              {rounds.length}
              <span className="muted">Y{current.year} · Q{current.quarter}</span>
              {showLiveRound && (
                <span className="muted" style={{ marginLeft: 8 }}>
                  · next round in progress
                </span>
              )}
            </>
          ) : liveRound ? (
            <>
              Round <b style={{ color: 'var(--text-hi)' }}>{liveRound.round_num}</b>
              <span className="muted" style={{ marginLeft: 6 }}>in progress</span>
            </>
          ) : (
            <span className="muted">No rounds yet</span>
          )}
        </div>
        <input
          type="range"
          min={0}
          max={Math.max(rounds.length - 1, 0)}
          value={currentSafeIdx}
          onChange={e => {
            setRoundIdx(Number(e.target.value));
            setFollow(false);
          }}
          disabled={!hasRounds}
        />
        <button
          className="primary"
          onClick={() => setPlaying(p => !p)}
          disabled={!hasRounds || (currentSafeIdx >= rounds.length - 1 && !playing)}
        >
          {playing
            ? 'Pause'
            : currentSafeIdx >= rounds.length - 1
              ? 'End'
              : 'Play'}
        </button>
        <div className="speed">
          <span>speed</span>
          <select
            value={speed}
            onChange={e => setSpeed(Number(e.target.value))}
            disabled={!hasRounds}
          >
            {SPEEDS.map(s => (
              <option key={s} value={s}>{s}×</option>
            ))}
          </select>
          <label
            className="follow-toggle"
            title="Auto-jump to the newest round as it streams in"
          >
            <input
              type="checkbox"
              checked={follow}
              onChange={e => setFollow(e.target.checked)}
            />
            <span>follow live</span>
          </label>
          <span
            className={clsx(
              'term-pill',
              termPillClass(current?.termination_reason),
            )}
            title={current?.done ? 'Episode terminated' : streamLabel(status)}
          >
            {streamPillLabel(status, current)}
          </span>
        </div>
      </div>

      {showShell && (
        <div className="layout">
          <div className="column">
            <RunControls
              modes={modes}
              status={status}
              lastError={lastError}
              currentRunId={runId}
              onStart={handleStart}
              onStop={handleStop}
            />
            {hasRounds ? (
              <>
                <RoundOverview
                  round={current}
                  prevRound={prev}
                  summary={episode.summary}
                />
                <RewardCard
                  reward={current.reward}
                  cumulative={current.cumulative_reward}
                />
              </>
            ) : (
              <div className="card">
                <h3>
                  Round summary
                  <span className="meta">awaiting first round</span>
                </h3>
                <div className="empty-state">
                  Pick a policy on the left and press <b>Start run</b>.
                </div>
              </div>
            )}
          </div>

          <div className="column">
            <div className="card">
              <h3>
                Sectors
                <span className="meta">
                  allocation vs critical · demand · surplus · wastage
                </span>
              </h3>
              {hasRounds ? (
                <>
                  {current.is_critical_failure && (
                    <div className="failure-banner">
                      <strong>Critical failure:</strong>{' '}
                      {current.failing_sectors.length > 0
                        ? `${current.failing_sectors.join(', ')} dropped below 40% of demand. `
                        : 'a sector dropped below 40% of demand. '}
                      Treasury was not debited (the round terminates before
                      allocation in Phase 5), so revenues for every sector are
                      zero.
                    </div>
                  )}
                  <div className="sector-grid">
                    {(episode.config.sectors || []).map(s => (
                      <SectorCard
                        key={s.name}
                        sector={sectorMap[s.name]}
                        allocation={current.allocations[s.name] || 0}
                        revenue={current.revenues[s.name] || 0}
                        revenueFactor={current.revenue_factors[s.name] || 0}
                        consumption={current.consumptions[s.name] || 0}
                        thresholds={current.thresholds[s.name]}
                        eventMultiplier={current.event_multipliers[s.name] || 1}
                        isFailureRound={current.is_critical_failure}
                        isFailingSector={current.failing_sectors.includes(s.name)}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <div className="empty-state">
                  Sectors render here once the first round arrives.
                </div>
              )}
            </div>

            {hasRounds && (
              <TimeSeries rounds={rounds} currentRound={current.round_num} />
            )}
          </div>

          <div className="column">
            <div className="card">
              <h3>
                {phasePanelRound
                  ? <>Round {phasePanelRound.round_num} decisions{showLiveRound && <span className="live-badge">LIVE</span>}</>
                  : 'Decisions'}
                <span className="meta">events → debate → vote</span>
              </h3>
              {phasePanelRound ? (
                <PhasePanel round={phasePanelRound} />
              ) : (
                <div className="empty-state">
                  Live debate, proposals, and votes will stream here as the
                  parliament deliberates.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function streamLabel(status) {
  switch (status) {
    case 'connecting':
      return 'Connecting…';
    case 'running':
      return 'Streaming live';
    case 'done':
      return 'Run complete';
    case 'error':
      return 'Run failed';
    default:
      return 'Idle';
  }
}

function streamPillLabel(status, current) {
  if (current?.done && current?.termination_reason) {
    return current.termination_reason;
  }
  return streamLabel(status).toLowerCase();
}
