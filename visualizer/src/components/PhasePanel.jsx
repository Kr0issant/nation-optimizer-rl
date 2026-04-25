import clsx from 'clsx';
import { fmt } from '../utils/format.js';

function EventCard({ event }) {
  const sevClass = `s${event.severity}`;
  const cls = event.is_positive ? 'positive' : event.severity >= 4 ? 'critical' : '';
  return (
    <div className={clsx('event', cls)}>
      <div className="ev-head">
        <span className="ev-name">{event.name}</span>
        <span className={clsx('ev-sev', sevClass)}>SEV {event.severity}</span>
      </div>
      <div className="ev-narrative">{event.narrative}</div>
      <div className="ev-mults">
        {Object.entries(event.affected_sectors).map(([k, v]) => (
          <span key={k}>{k} ×{v.toFixed(2)}</span>
        ))}
      </div>
      {event.treasury_injection > 0 && (
        <div className="ev-injection">+{fmt(event.treasury_injection)} treasury injection</div>
      )}
    </div>
  );
}

function ProposalCard({ proposal, voteResult, votes, ownerDept }) {
  const status = voteResult?.status || 'PENDING';
  const cls = status === 'APPROVED' ? 'approved' : status.startsWith('REJ') || status.startsWith('AUTO') ? 'rejected' : '';
  const voteList = votes.filter(v => v.proposal_id === proposal.proposal_id);

  return (
    <div className={clsx('proposal', cls)}>
      <div className="p-head">
        <span className="p-name">{proposal.department}</span>
        <span className="p-amount">{fmt(proposal.amount)}</span>
      </div>
      <div className="p-just">{proposal.justification}</div>
      <div className="p-votes">
        {voteList.map(v => (
          <span
            key={`${v.proposal_id}-${v.agent_id}`}
            className={clsx('vote-chip', v.vote, { own: v.department === ownerDept })}
            title={v.department === ownerDept ? 'Self-vote (must abstain)' : `${v.department}: ${v.vote}`}
          >
            {v.department.slice(0, 3)}: {v.vote === 'ABSTAIN' ? '—' : v.vote === 'YES' ? '✓' : '✗'}
          </span>
        ))}
      </div>
      {voteResult && (
        <div className="p-tally">
          {status} · {voteResult.yes} yes / {voteResult.no} no / {voteResult.abstain} abstain
        </div>
      )}
    </div>
  );
}

export default function PhasePanel({ round }) {
  if (!round) return null;

  const events = round.events || [];
  const debate = round.debate || [];
  const proposals = round.proposals || [];
  const votes = round.votes || [];
  const voteResults = round.vote_results || [];
  const proposalOrder = round.proposal_order || [];
  const phase = round._phase; // only present on live partial rounds

  return (
    <div className="phase-panel">
      <div className="phase-block">
        <h4>Phase 1 — Events{phase === 'events' && <LiveDot />}</h4>
        {events.length === 0 ? (
          <div style={{ color: 'var(--text-mute)', fontSize: 12 }}>No events this round (40% baseline).</div>
        ) : (
          events.map((e, i) => <EventCard key={`${round.round_num}-${i}`} event={e} />)
        )}
      </div>

      <div className="phase-block">
        <h4>Phase 2 — Debate{phase === 'debate' && <LiveDot />}</h4>
        {debate.length === 0 && phase !== 'debate' ? (
          <div style={{ color: 'var(--text-mute)', fontSize: 12 }}>All ministers stayed silent.</div>
        ) : debate.length === 0 && phase === 'debate' ? (
          <div style={{ color: 'var(--text-mute)', fontSize: 12 }}>Waiting for first minister to speak…</div>
        ) : (
          debate.map((m, i) => (
            <div key={i} className="debate-msg">
              <div className="who">{m.department || m.agent_id}</div>
              <div className="text">{m.message}</div>
            </div>
          ))
        )}
      </div>

      <div className="phase-block">
        <h4>Phase 3–4 — Proposals & Votes{(phase === 'proposals' || phase === 'votes') && <LiveDot />}</h4>
        {proposalOrder.length > 0 && (
          <div style={{ color: 'var(--text-mute)', fontSize: 11, marginBottom: 6 }}>
            rotating order: {proposalOrder.join(' → ')}
          </div>
        )}
        {proposals.length === 0 && (phase === 'proposals' || phase === 'votes') && (
          <div style={{ color: 'var(--text-mute)', fontSize: 12 }}>Waiting for proposals…</div>
        )}
        {proposals.map(p => {
          const result = voteResults.find(v => v.proposal_id === p.proposal_id);
          return (
            <ProposalCard
              key={p.proposal_id || `p-${proposals.indexOf(p)}`}
              proposal={p}
              voteResult={result}
              votes={votes}
              ownerDept={p.department}
            />
          );
        })}
      </div>
    </div>
  );
}

function LiveDot() {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: 'var(--accent-bad)',
        marginLeft: 6,
        verticalAlign: 'middle',
        animation: 'liveBlink 1.4s ease-in-out infinite',
      }}
      title="Streaming live"
    />
  );
}
