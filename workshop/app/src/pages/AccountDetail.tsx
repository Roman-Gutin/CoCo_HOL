import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import HealthBadge from "../components/HealthBadge";
import { executeSQL } from "../lib/snowflake";

/**
 * Account drill-down page.
 * Fetches live data from Snowflake, falling back to mock data on error.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type HealthStatus = "at_risk" | "expansion" | "healthy" | "attention";

interface AccountInfo {
  name: string;
  industry: string;
  arr: number;
  healthScore: number;
  status: HealthStatus;
  licensedSeats: number;
  activeSeats: number;
  seatUtilizationPct: number;
  avgSentiment: number;
  competitorMentioned: boolean;
  expansionSignal: boolean;
  aeChangedRecently: boolean;
  currentAe: string;
  npsScore: number;
  featureBreadthPct: number;
}

interface Ticket {
  id: string;
  priority: string;
  text: string;
  date: string;
  status: string;
}

interface GongCall {
  callId: string;
  date: string;
  type: string;
  excerpt: string;
  attendees: string;
}

interface AeAssignment {
  employeeName: string;
  role: string;
  assignedDate: string;
  unassignedDate: string | null;
  isCurrent: boolean;
}

// ---------------------------------------------------------------------------
// Mock data — fallback
// ---------------------------------------------------------------------------

const MOCK_ACCOUNT: AccountInfo = {
  name: "Meridian Media Group",
  industry: "Media",
  arr: 340_000,
  healthScore: 22,
  status: "at_risk",
  licensedSeats: 80,
  activeSeats: 31,
  seatUtilizationPct: 39,
  avgSentiment: -0.5,
  competitorMentioned: true,
  expansionSignal: false,
  aeChangedRecently: false,
  currentAe: "Jane Smith",
  npsScore: 20,
  featureBreadthPct: 30,
};

const MOCK_TICKETS: Ticket[] = [
  { id: "TKT-412", priority: "P1", text: "Canvas export failing for large files — entire team blocked", date: "Mar 11", status: "Open" },
  { id: "TKT-398", priority: "P2", text: "Flow automation triggers not firing after update", date: "Mar 8", status: "Open" },
  { id: "TKT-385", priority: "P2", text: "Slow load times on Canvas dashboard — 10+ seconds", date: "Mar 4", status: "In Progress" },
  { id: "TKT-371", priority: "P3", text: "Feature request: bulk export for Canvas assets", date: "Feb 27", status: "Open" },
];

const MOCK_GONG: GongCall[] = [
  {
    callId: "G-001",
    date: "Mar 7",
    type: "Check-in",
    excerpt:
      "Sarah (new VP Design) mentioned they're evaluating SketchFlow for the design team. Previous champion Jake left in February. Team morale around Canvas is low — 'we spend more time fighting the tool than using it.'",
    attendees: "",
  },
  {
    callId: "G-002",
    date: "Feb 20",
    type: "QBR",
    excerpt:
      "Usage numbers came up — they acknowledged the decline. CFO asked about contract flexibility. They want to see a 'clear improvement plan' before renewal in June.",
    attendees: "",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Escape single quotes in a string for safe SQL interpolation */
function escapeSql(s: string): string {
  return s.replace(/'/g, "''");
}

function deriveHealthStatus(row: Record<string, unknown>): HealthStatus {
  const competitorMentioned = row.COMPETITOR_MENTIONED === true || row.COMPETITOR_MENTIONED === "true";
  const avgSentiment = Number(row.AVG_SENTIMENT ?? 0);
  const aeChangedRecently = row.AE_CHANGED_RECENTLY === true || row.AE_CHANGED_RECENTLY === "true";
  const expansionSignal = row.EXPANSION_SIGNAL === true || row.EXPANSION_SIGNAL === "true";

  if (competitorMentioned || avgSentiment < -0.3 || aeChangedRecently) return "at_risk";
  if (expansionSignal) return "expansion";
  return "healthy";
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AccountDetail() {
  const { id } = useParams<{ id: string }>();
  const accountName = decodeURIComponent(id ?? "");

  const [account, setAccount] = useState<AccountInfo>(MOCK_ACCOUNT);
  const [tickets, setTickets] = useState<Ticket[]>(MOCK_TICKETS);
  const [gongCalls, setGongCalls] = useState<GongCall[]>(MOCK_GONG);
  const [aeHistory, setAeHistory] = useState<AeAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const escaped = escapeSql(accountName);

    async function fetchAll() {
      try {
        // Fire all queries in parallel
        const [healthResult, ticketsResult, gongResult, aeResult] =
          await Promise.all([
            executeSQL(
              `SELECT * FROM MARTS.MART_ACCOUNT_HEALTH WHERE account_name = '${escaped}'`
            ),
            executeSQL(
              `SELECT ticket_id, ticket_text, priority, status, created_at
               FROM RAW.SUPPORT_TICKETS
               WHERE account_name = '${escaped}'
               ORDER BY created_at DESC LIMIT 10`
            ),
            executeSQL(
              `SELECT call_id, call_type, call_date, transcript_excerpt, attendees
               FROM RAW.GONG_TRANSCRIPTS
               WHERE account_name = '${escaped}'
               ORDER BY call_date DESC LIMIT 5`
            ),
            executeSQL(
              `SELECT employee_name, role, assigned_date, unassigned_date, is_current
               FROM RAW.ACCOUNT_ASSIGNMENTS
               WHERE account_name = '${escaped}'
               ORDER BY assigned_date DESC`
            ),
          ]);

        if (cancelled) return;

        // Map account health
        if (healthResult.rows.length > 0 && healthResult.rows[0]) {
          const r = healthResult.rows[0] as Record<string, unknown>;
          const seatUtil = Number(r.SEAT_UTILIZATION_PCT ?? 0);
          setAccount({
            name: String(r.ACCOUNT_NAME ?? accountName),
            industry: String(r.INDUSTRY ?? ""),
            arr: Number(r.ARR ?? 0),
            healthScore: Math.round(
              seatUtil * 0.3 +
              Number(r.NPS_SCORE ?? 50) * 0.3 +
              Number(r.FEATURE_BREADTH_PCT ?? 50) * 0.4
            ),
            status: deriveHealthStatus(r),
            licensedSeats: Number(r.LICENSED_SEATS ?? 0),
            activeSeats: Math.round(
              (Number(r.LICENSED_SEATS ?? 0) * seatUtil) / 100
            ),
            seatUtilizationPct: seatUtil,
            avgSentiment: Number(r.AVG_SENTIMENT ?? 0),
            competitorMentioned: r.COMPETITOR_MENTIONED === true || r.COMPETITOR_MENTIONED === "true",
            expansionSignal: r.EXPANSION_SIGNAL === true || r.EXPANSION_SIGNAL === "true",
            aeChangedRecently: r.AE_CHANGED_RECENTLY === true || r.AE_CHANGED_RECENTLY === "true",
            currentAe: String(r.CURRENT_AE ?? ""),
            npsScore: Number(r.NPS_SCORE ?? 0),
            featureBreadthPct: Number(r.FEATURE_BREADTH_PCT ?? 0),
          });
        }

        // Map tickets
        if (ticketsResult.rows.length > 0) {
          setTickets(
            ticketsResult.rows.filter(Boolean).map((r) => ({
              id: String(r.TICKET_ID ?? ""),
              priority: String(r.PRIORITY ?? ""),
              text: String(r.TICKET_TEXT ?? ""),
              date: String(r.CREATED_AT ?? "").slice(0, 10),
              status: String(r.STATUS ?? ""),
            }))
          );
        }

        // Map gong calls
        if (gongResult.rows.length > 0) {
          setGongCalls(
            gongResult.rows.filter(Boolean).map((r) => ({
              callId: String(r.CALL_ID ?? ""),
              date: String(r.CALL_DATE ?? "").slice(0, 10),
              type: String(r.CALL_TYPE ?? ""),
              excerpt: String(r.TRANSCRIPT_EXCERPT ?? ""),
              attendees: String(r.ATTENDEES ?? ""),
            }))
          );
        }

        // Map AE history
        if (aeResult.rows.length > 0) {
          setAeHistory(
            aeResult.rows.filter(Boolean).map((r) => ({
              employeeName: String(r.EMPLOYEE_NAME ?? ""),
              role: String(r.ROLE ?? ""),
              assignedDate: String(r.ASSIGNED_DATE ?? "").slice(0, 10),
              unassignedDate: r.UNASSIGNED_DATE
                ? String(r.UNASSIGNED_DATE).slice(0, 10)
                : null,
              isCurrent: r.IS_CURRENT === true || r.IS_CURRENT === "true",
            }))
          );
        }

        setError(null);
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to fetch account detail from Snowflake:", err);
          setError(
            err instanceof Error ? err.message : "Failed to load live data"
          );
          // Keep mock data as fallback
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (accountName) {
      fetchAll();
    } else {
      setLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [accountName]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-sm text-gray-500 animate-pulse">
          Loading account details from Snowflake...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link to="/" className="hover:text-gray-300">
          Portfolio
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-300">{account.name}</span>
      </nav>

      {error && (
        <div className="rounded-lg border border-amber-700/50 bg-amber-900/20 px-4 py-3 text-sm text-amber-300">
          <strong>Warning:</strong> Could not load live data from Snowflake.
          Showing mock data.{" "}
          <span className="text-amber-500 text-xs block mt-1">{error}</span>
        </div>
      )}

      {/* Account Header */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{account.name}</h1>
              <HealthBadge status={account.status} />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              {account.industry}
              {account.currentAe && (
                <span className="ml-3 text-gray-600">
                  AE: {account.currentAe}
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-8 text-center">
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500">ARR</p>
              <p className="text-xl font-bold text-gray-200">
                ${account.arr.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500">Health Score</p>
              <p
                className={`text-xl font-bold ${
                  account.healthScore >= 70
                    ? "text-emerald-400"
                    : account.healthScore >= 45
                    ? "text-amber-400"
                    : "text-red-400"
                }`}
              >
                {account.healthScore}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500">Seat Utilization</p>
              <p className="text-xl font-bold text-gray-200">
                {account.activeSeats}/{account.licensedSeats}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500">NPS</p>
              <p className="text-xl font-bold text-gray-200">
                {account.npsScore}
              </p>
            </div>
          </div>
        </div>

        {/* Signal badges */}
        <div className="mt-4 flex gap-2 flex-wrap">
          {account.competitorMentioned && (
            <span className="rounded-md bg-red-900/30 border border-red-800/50 px-2.5 py-1 text-xs font-medium text-red-400">
              Competitor Mentioned
            </span>
          )}
          {account.aeChangedRecently && (
            <span className="rounded-md bg-amber-900/30 border border-amber-800/50 px-2.5 py-1 text-xs font-medium text-amber-400">
              AE Changed Recently
            </span>
          )}
          {account.expansionSignal && (
            <span className="rounded-md bg-emerald-900/30 border border-emerald-800/50 px-2.5 py-1 text-xs font-medium text-emerald-400">
              Expansion Signal
            </span>
          )}
          <span className="rounded-md bg-gray-800 px-2.5 py-1 text-xs font-medium text-gray-400">
            Sentiment: {account.avgSentiment.toFixed(2)}
          </span>
          <span className="rounded-md bg-gray-800 px-2.5 py-1 text-xs font-medium text-gray-400">
            Feature Breadth: {account.featureBreadthPct}%
          </span>
        </div>
      </div>

      {/* Two-column layout: tickets + gong */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Support Tickets */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Recent Support Tickets</h2>
          <div className="space-y-3">
            {tickets.length === 0 && (
              <p className="text-sm text-gray-600 italic">No recent tickets.</p>
            )}
            {tickets.map((t) => (
              <div key={t.id} className="rounded-lg border border-gray-800 p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono text-gray-500">{t.id}</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold ${
                        t.priority === "P1"
                          ? "text-red-400"
                          : t.priority === "P2"
                          ? "text-amber-400"
                          : "text-gray-500"
                      }`}
                    >
                      {t.priority}
                    </span>
                    {t.status && (
                      <span className="text-xs text-gray-600 bg-gray-800 rounded px-1.5 py-0.5">
                        {t.status}
                      </span>
                    )}
                    <span className="text-xs text-gray-600">{t.date}</span>
                  </div>
                </div>
                <p className="text-sm text-gray-300">{t.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* AE History */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">AE Assignment History</h2>
          {aeHistory.length === 0 ? (
            <p className="text-sm text-gray-600 italic">No assignment history available.</p>
          ) : (
            <div className="space-y-2">
              {aeHistory.map((ae, i) => (
                <div
                  key={i}
                  className={`rounded-lg border p-3 ${
                    ae.isCurrent
                      ? "border-indigo-700/50 bg-indigo-900/10"
                      : "border-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-200">
                      {ae.employeeName}
                      {ae.isCurrent && (
                        <span className="ml-2 text-xs text-indigo-400">(current)</span>
                      )}
                    </span>
                    <span className="text-xs text-gray-500">{ae.role}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {ae.assignedDate}
                    {ae.unassignedDate ? ` — ${ae.unassignedDate}` : " — present"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Gong Call Excerpts */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Gong Call Excerpts</h2>
        <div className="space-y-4">
          {gongCalls.length === 0 && (
            <p className="text-sm text-gray-600 italic">No recent Gong calls.</p>
          )}
          {gongCalls.map((g, i) => (
            <div key={i} className="rounded-lg border border-gray-800 p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="rounded-md bg-gray-800 px-2 py-0.5 text-xs font-medium text-gray-400">
                  {g.type}
                </span>
                <span className="text-xs text-gray-600">{g.date}</span>
                {g.attendees && (
                  <span className="text-xs text-gray-600">{g.attendees}</span>
                )}
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">{g.excerpt}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Account name debug info */}
      <p className="text-xs text-gray-700">Account: {accountName}</p>
    </div>
  );
}
