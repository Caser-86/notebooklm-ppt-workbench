type JobTimelineProps = {
  status: string;
  attentionReason?: string;
};

export function JobTimeline({ status, attentionReason }: JobTimelineProps) {
  return (
    <section>
      <h3>Job status</h3>
      <p>{status}</p>
      {attentionReason ? <p>{attentionReason}</p> : null}
      {status === "needs_attention" ? <button>Resume job</button> : null}
    </section>
  );
}
