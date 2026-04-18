type JobTimelineProps = {
  status: string;
  attentionReason?: string;
};

import { useI18n } from "../lib/i18n";

export function JobTimeline({ status, attentionReason }: JobTimelineProps) {
  const { messages } = useI18n();
  const statusLabel =
    status === "needs_attention"
      ? messages.jobTimeline.statusNeedsAttention
      : status === "ready_to_generate"
        ? messages.jobTimeline.statusReadyToGenerate
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
      </div>
    </section>
  );
}
