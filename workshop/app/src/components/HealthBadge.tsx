/**
 * HealthBadge — renders a colored pill based on account health status.
 */

type HealthStatus = "at_risk" | "expansion" | "healthy" | "attention";

const STYLES: Record<HealthStatus, string> = {
  at_risk: "bg-red-500/15 text-red-400 ring-red-500/30",
  expansion: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/30",
  healthy: "bg-blue-500/15 text-blue-400 ring-blue-500/30",
  attention: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
};

const LABELS: Record<HealthStatus, string> = {
  at_risk: "At Risk",
  expansion: "Expansion",
  healthy: "Healthy",
  attention: "Attention",
};

interface Props {
  status: HealthStatus;
}

export default function HealthBadge({ status }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
