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

  return (
    <div className="phase-panel">
      <div className="phase-block">
        <h4>Phase 1 — Events</h4>
        {round.events.length === 0 ? (
          <div style={{ color: 'var(--text-mute)', fontSize: 12 }}>No events this round (40% baseline).</div>
        ) : (
          round.events.map((e, i) => <EventCard key={`${round.round_num}-${i}`} event={e} />)
        )}
      </div>

      <div className="phase-block">
        <h4>Phase 2 — Debate</h4>
        {round.debate.length === 0 ? (
          <div style={{ color: 'var(--text-mute)', fontSize: 12 }}>All ministers stayed silent.</div>
        ) : (
          round.debate.map((m, i) => (
            <div key={i} className="debate-msg">
              <div className="who">{m.department}</div>
              <div className="text">{m.message}</div>
            </div>
          ))
        )}
      </div>

      <div className="phase-block">
        <h4>Phase 3–4 — Proposals & Votes</h4>
        <div style={{ color: 'var(--text-mute)', fontSize: 11, marginBottom: 6 }}>
          rotating order: {round.proposal_order.join(' → ')}
        </div>
        {round.proposals.map(p => {
          const result = round.vote_results.find(v => v.proposal_id === p.proposal_id);
          return (
            <ProposalCard
              key={p.proposal_id}
              proposal={p}
              voteResult={result}
              votes={round.votes}
              ownerDept={p.department}
            />
          );
        })}
      </div>
    </div>
  );
}
