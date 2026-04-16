type JobTimelineProps = {
  status: string;
  attentionReason?: string;
};

export function JobTimeline({ status, attentionReason }: JobTimelineProps) {
  const statusLabel =
    status === "needs_attention"
      ? "Needs your action"
      : status === "ready_to_generate"
        ? "Ready for NotebookLM"
        : status;

  const attentionLabel =
    attentionReason === "browser_login_required"
      ? "Sign in to Google and finish this step in NotebookLM."
      : attentionReason;

  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">Status</p>
        <h3>Job status</h3>
      </div>
      <div className="status-block">
        <p className="status-pill">{statusLabel}</p>
        {attentionLabel ? <p>{attentionLabel}</p> : null}
        {status === "needs_attention" ? (
          <button className="secondary-action" type="button">
            I finished this in NotebookLM
          </button>
        ) : null}
      </div>
    </section>
  );
}
