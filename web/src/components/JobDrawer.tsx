import { useMemo } from "react";

import { useI18n } from "../lib/i18n";
import type { JobRead } from "../lib/types";

type JobDrawerProps = {
  open: boolean;
  jobs: JobRead[];
  failedOnly: boolean;
  onClose: () => void;
  onToggleFailedOnly: () => void;
  onRetry?: (jobId: number) => void;
  onCancel?: (jobId: number) => void;
  onDelete?: (jobId: number) => void;
};

export function JobDrawer({
  open,
  jobs,
  failedOnly,
  onClose,
  onToggleFailedOnly,
  onRetry,
  onCancel,
  onDelete,
}: JobDrawerProps) {
  const { locale, messages } = useI18n();

  const visibleJobs = useMemo(
    () => (failedOnly ? jobs.filter((job) => job.status === "failed") : jobs),
    [failedOnly, jobs],
  );

  const formatJobTimestamp = (createdAt: string) =>
    new Intl.DateTimeFormat(locale, {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(createdAt));

  return (
    <aside className={open ? "job-drawer is-open" : "job-drawer"} aria-hidden={!open}>
      <div className="job-drawer__header">
        <h3>{messages.jobTimeline.drawerTitle}</h3>
        <button className="secondary-action" type="button" onClick={onClose}>
          {messages.jobTimeline.close}
        </button>
      </div>
      <div className="job-drawer__filters">
        <button
          className={failedOnly ? "secondary-action" : "primary-action"}
          type="button"
          onClick={() => failedOnly && onToggleFailedOnly()}
        >
          {messages.jobTimeline.allJobs}
        </button>
        <button
          className={failedOnly ? "primary-action" : "secondary-action"}
          type="button"
          onClick={() => !failedOnly && onToggleFailedOnly()}
        >
          {messages.jobTimeline.failedOnly}
        </button>
      </div>
      <div className="job-drawer__list">
        <ul>
          {visibleJobs.map((job) => (
            <li key={job.id} className="job-drawer__item">
              <div className="job-drawer__meta">
                <span>{job.job_type}</span>
                <span>{job.status}</span>
                <span>{formatJobTimestamp(job.created_at)}</span>
              </div>
              {job.error_message ? (
                <p>
                  {messages.jobTimeline.failedReason}: {job.error_message}
                </p>
              ) : null}
              {job.status === "failed" && onRetry ? (
                <button className="secondary-action" type="button" onClick={() => onRetry(job.id)}>
                  {messages.jobTimeline.retry}
                </button>
              ) : null}
              {job.status === "queued" && onCancel ? (
                <button className="secondary-action" type="button" onClick={() => onCancel(job.id)}>
                  {messages.jobTimeline.cancel}
                </button>
              ) : null}
              {["succeeded", "failed", "cancelled"].includes(job.status) && onDelete ? (
                <button className="secondary-action" type="button" onClick={() => onDelete(job.id)}>
                  {messages.jobTimeline.clear}
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
