type JobTimelineProps = {
  status: string;
  attentionReason?: string;
  jobs?: Array<{ id: number; job_type: string; status: string }>;
};

import { useI18n } from "../lib/i18n";

export function JobTimeline({ status, attentionReason, jobs = [] }: JobTimelineProps) {
  const { messages } = useI18n();
  const statusLabel =
    status === "needs_attention"
      ? messages.jobTimeline.statusNeedsAttention
      : status === "ready_to_generate"
        ? messages.jobTimeline.statusReadyToGenerate
        : status === "queued"
          ? messages.jobTimeline.statusQueued
          : status === "running"
            ? messages.jobTimeline.statusRunning
            : status === "succeeded"
              ? messages.jobTimeline.statusSucceeded
              : status === "failed"
                ? messages.jobTimeline.statusFailed
        : status;

  const attentionLabel =
    attentionReason === "browser_login_required"
      ? messages.jobTimeline.browserLoginRequired
      : attentionReason;

  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">{messages.jobTimeline.eyebrow}</p>
        <h3>{messages.jobTimeline.title}</h3>
      </div>
      <div className="status-block">
        <p className="status-pill">{statusLabel}</p>
        {attentionLabel ? <p>{attentionLabel}</p> : null}
        {status === "needs_attention" ? (
          <button className="secondary-action" type="button">
            {messages.jobTimeline.finishInNotebooklm}
          </button>
        ) : null}
        {jobs.length > 0 ? (
          <div className="rebuild-history">
            <h4>{messages.jobTimeline.recentJobs}</h4>
            <ul>
              {jobs.slice(0, 5).map((job) => (
                <li key={job.id}>
                  <span>{job.job_type}</span>
                  <span>{job.status}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
}
