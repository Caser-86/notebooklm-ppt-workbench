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
    <section>
      <h3>Job status</h3>
      <p>{statusLabel}</p>
      {attentionLabel ? <p>{attentionLabel}</p> : null}
      {status === "needs_attention" ? <button>I finished this in NotebookLM</button> : null}
    </section>
  );
}
