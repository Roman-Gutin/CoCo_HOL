import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import HealthBadge from "../components/HealthBadge";
import { executeSQL } from "../lib/snowflake";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type HealthStatus = "at_risk" | "expansion" | "healthy" | "attention";

interface Account {
  id: string;
  name: string;
  industry: string;
  arr: number;
  healthScore: number;
  status: HealthStatus;
  usageTrend: number;
  openTickets: number;
  seatUtilization: number;
  avgSentiment: number;
  competitorMentioned: boolean;
  expansionSignal: boolean;
  aeChangedRecently: boolean;
  currentAe: string;
  pipelineAmount: number;
  npsScore: number;
  featureBreadthPct: number;
  avgDiscountPct: number;
  overdueInvoices: number;
}

// ---------------------------------------------------------------------------
// Mock data — fallback when Snowflake is unavailable
// ---------------------------------------------------------------------------

const MOCK_ACCOUNTS: Account[] = [
  { id: "acct-001", name: "Meridian Media Group", industry: "Media", arr: 340_000, healthScore: 22, status: "at_risk", usageTrend: -38, openTickets: 7, seatUtilization: 39, avgSentiment: -0.5, competitorMentioned: true, expansionSignal: false, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 20, featureBreadthPct: 30, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-002", name: "Cascade Financial", industry: "Finance", arr: 520_000, healthScore: 31, status: "at_risk", usageTrend: -12, openTickets: 5, seatUtilization: 45, avgSentiment: -0.4, competitorMentioned: false, expansionSignal: false, aeChangedRecently: true, currentAe: "", pipelineAmount: 0, npsScore: 25, featureBreadthPct: 40, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-003", name: "Beacon Logistics", industry: "Logistics", arr: 180_000, healthScore: 28, status: "at_risk", usageTrend: -45, openTickets: 4, seatUtilization: 30, avgSentiment: -0.6, competitorMentioned: true, expansionSignal: false, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 18, featureBreadthPct: 25, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-004", name: "Prism Retail", industry: "Retail", arr: 85_000, healthScore: 35, status: "at_risk", usageTrend: -18, openTickets: 0, seatUtilization: 40, avgSentiment: -0.35, competitorMentioned: false, expansionSignal: false, aeChangedRecently: true, currentAe: "", pipelineAmount: 0, npsScore: 30, featureBreadthPct: 35, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-005", name: "Atlas Digital", industry: "Technology", arr: 290_000, healthScore: 88, status: "expansion", usageTrend: 15, openTickets: 2, seatUtilization: 90, avgSentiment: 0.7, competitorMentioned: false, expansionSignal: true, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 85, featureBreadthPct: 80, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-006", name: "Summit Healthcare", industry: "Healthcare", arr: 210_000, healthScore: 82, status: "expansion", usageTrend: 22, openTickets: 3, seatUtilization: 85, avgSentiment: 0.6, competitorMentioned: false, expansionSignal: true, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 80, featureBreadthPct: 75, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-007", name: "Voyager Entertainment", industry: "Entertainment", arr: 780_000, healthScore: 91, status: "expansion", usageTrend: 5, openTickets: 0, seatUtilization: 95, avgSentiment: 0.8, competitorMentioned: false, expansionSignal: true, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 90, featureBreadthPct: 90, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-008", name: "Ironclad Manufacturing", industry: "Manufacturing", arr: 150_000, healthScore: 76, status: "expansion", usageTrend: 10, openTickets: 1, seatUtilization: 80, avgSentiment: 0.5, competitorMentioned: false, expansionSignal: true, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 75, featureBreadthPct: 70, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-009", name: "Northstar Consulting", industry: "Consulting", arr: 260_000, healthScore: 70, status: "healthy", usageTrend: 2, openTickets: 1, seatUtilization: 70, avgSentiment: 0.3, competitorMentioned: false, expansionSignal: false, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 70, featureBreadthPct: 60, avgDiscountPct: 0, overdueInvoices: 0 },
  { id: "acct-010", name: "Ridgeline Media", industry: "Media", arr: 195_000, healthScore: 72, status: "healthy", usageTrend: 1, openTickets: 0, seatUtilization: 72, avgSentiment: 0.2, competitorMentioned: false, expansionSignal: false, aeChangedRecently: false, currentAe: "", pipelineAmount: 0, npsScore: 72, featureBreadthPct: 55, avgDiscountPct: 0, overdueInvoices: 0 },
];

// ---------------------------------------------------------------------------
// Derive health status from raw Snowflake row
// ---------------------------------------------------------------------------

function deriveHealthStatus(row: Record<string, unknown>): HealthStatus {
  const competitorMentioned = row.COMPETITOR_MENTIONED === true || row.COMPETITOR_MENTIONED === "true";
  const avgSentiment = Number(row.AVG_SENTIMENT ?? 0);
  const aeChangedRecently = row.AE_CHANGED_RECENTLY === true || row.AE_CHANGED_RECENTLY === "true";
  const expansionSignal = row.EXPANSION_SIGNAL === true || row.EXPANSION_SIGNAL === "true";

  if (competitorMentioned || avgSentiment < -0.3 || aeChangedRecently) {
    return "at_risk";
  }
  if (expansionSignal) {
    return "expansion";
  }
  return "healthy";
}

function mapRowToAccount(row: Record<string, unknown>, index: number): Account {
  const status = deriveHealthStatus(row);
  const seatUtil = Number(row.SEAT_UTILIZATION_PCT ?? 0);

  return {
    id: String(row.ACCOUNT_NAME ?? `acct-${index}`),
    name: String(row.ACCOUNT_NAME ?? "Unknown"),
    industry: String(row.INDUSTRY ?? ""),
    arr: Number(row.ARR ?? 0),
    healthScore: Math.round(seatUtil * 0.3 + Number(row.NPS_SCORE ?? 50) * 0.3 + Number(row.FEATURE_BREADTH_PCT ?? 50) * 0.4),
    status,
    usageTrend: Number(row.USAGE_TREND_WOW_PCT ?? 0),
    openTickets: 0, // not in this query
    seatUtilization: seatUtil,
    avgSentiment: Number(row.AVG_SENTIMENT ?? 0),
    competitorMentioned: row.COMPETITOR_MENTIONED === true || row.COMPETITOR_MENTIONED === "true",
    expansionSignal: row.EXPANSION_SIGNAL === true || row.EXPANSION_SIGNAL === "true",
    aeChangedRecently: row.AE_CHANGED_RECENTLY === true || row.AE_CHANGED_RECENTLY === "true",
    currentAe: String(row.CURRENT_AE ?? ""),
    pipelineAmount: Number(row.PIPELINE_AMOUNT ?? 0),
    npsScore: Number(row.NPS_SCORE ?? 0),
    featureBreadthPct: Number(row.FEATURE_BREADTH_PCT ?? 0),
    avgDiscountPct: Number(row.AVG_DISCOUNT_PCT ?? 0),
    overdueInvoices: Number(row.OVERDUE_INVOICES ?? 0),
  };
}

// ---------------------------------------------------------------------------
// Summary Cards
// ---------------------------------------------------------------------------

function SummaryCards({ accounts }: { accounts: Account[] }) {
  const total = accounts.length;
  const at_risk = accounts.filter((a) => a.status === "at_risk").length;
  const expansion = accounts.filter((a) => a.status === "expansion").length;
  const healthy = accounts.filter((a) => a.status === "healthy").length;

  const cards: { label: string; value: number; color: string }[] = [
    { label: "Total Accounts", value: total, color: "text-gray-100" },
    { label: "At Risk", value: at_risk, color: "text-red-400" },
    { label: "Expansion Ready", value: expansion, color: "text-emerald-400" },
    { label: "Healthy", value: healthy, color: "text-blue-400" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-xl border border-gray-800 bg-gray-900 p-5 card-hover"
        >
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
            {c.label}
          </p>
          <p className={`mt-2 text-3xl font-bold ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Risk Heatmap placeholder
// ---------------------------------------------------------------------------

const SIGNAL_COLS = [
  { key: "usage",     label: "Usage Trend" },
  { key: "sentiment", label: "Sentiment" },
  { key: "features",  label: "Feature Adoption" },
  { key: "ae",        label: "AE Stability" },
  { key: "payment",   label: "Payment Health" },
  { key: "nps",       label: "NPS" },
] as const;

function signalScore(acct: Account, key: string): number {
  // Returns 0-1 where 1 = healthy, 0 = critical
  switch (key) {
    case "usage":     return Math.max(0, Math.min(1, (acct.usageTrend + 30) / 60));
    case "sentiment": return Math.max(0, Math.min(1, (acct.avgSentiment + 1) / 2));
    case "features":  return Math.max(0, Math.min(1, acct.featureBreadthPct / 100));
    case "ae":        return acct.aeChangedRecently ? 0.15 : 1;
    case "payment":   return acct.overdueInvoices > 0 ? 0.1 : 1;
    case "nps":       return Math.max(0, Math.min(1, acct.npsScore / 10));
    default:          return 0.5;
  }
}

function heatColor(score: number): string {
  if (score >= 0.7) return "bg-emerald-500/80";
  if (score >= 0.5) return "bg-emerald-500/30";
  if (score >= 0.3) return "bg-yellow-500/50";
  if (score >= 0.15) return "bg-orange-500/60";
  return "bg-red-500/70";
}

function RiskHeatmap({ accounts }: { accounts: Account[] }) {
  const sorted = [...accounts].sort((a, b) => {
    const aAvg = SIGNAL_COLS.reduce((s, c) => s + signalScore(a, c.key), 0) / SIGNAL_COLS.length;
    const bAvg = SIGNAL_COLS.reduce((s, c) => s + signalScore(b, c.key), 0) / SIGNAL_COLS.length;
    return aAvg - bAvg;
  });

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-300">Account Health Heatmap</h2>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="inline-block w-3 h-3 rounded bg-red-500/70" /> Critical
          <span className="inline-block w-3 h-3 rounded bg-orange-500/60" /> Warning
          <span className="inline-block w-3 h-3 rounded bg-yellow-500/50" /> Fair
          <span className="inline-block w-3 h-3 rounded bg-emerald-500/80" /> Healthy
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="text-left text-gray-500 font-medium py-2 pr-4 w-48">Account</th>
              <th className="text-left text-gray-500 font-medium py-2 pr-2 w-16">ARR</th>
              {SIGNAL_COLS.map(c => (
                <th key={c.key} className="text-center text-gray-500 font-medium py-2 px-1">{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(acct => (
              <tr key={acct.id} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                <td className="py-1.5 pr-4">
                  <Link to={`/account/${encodeURIComponent(acct.name)}`} className="text-gray-200 hover:text-white">
                    {acct.name}
                  </Link>
                </td>
                <td className="py-1.5 pr-2 text-gray-400">${(acct.arr / 1000).toFixed(0)}K</td>
                {SIGNAL_COLS.map(c => {
                  const score = signalScore(acct, c.key);
                  return (
                    <td key={c.key} className="py-1.5 px-1">
                      <div
                        className={`mx-auto w-full h-6 rounded ${heatColor(score)} flex items-center justify-center`}
                        title={`${c.label}: ${(score * 100).toFixed(0)}%`}
                      >
                        <span className="text-[10px] text-white/80 font-mono">
                          {c.key === "ae" ? (acct.aeChangedRecently ? "CHG" : "OK") :
                           c.key === "payment" ? (acct.overdueInvoices > 0 ? "DUE" : "OK") :
                           (score * 100).toFixed(0)}
                        </span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Account Table
// ---------------------------------------------------------------------------

function formatCurrency(n: number): string {
  return "$" + n.toLocaleString();
}

function AccountTable({ accounts }: { accounts: Account[] }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-800">
        <h2 className="text-sm font-semibold text-gray-300">All Accounts</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-left text-xs uppercase tracking-wider text-gray-500">
              <th className="px-6 py-3 font-medium">Account</th>
              <th className="px-6 py-3 font-medium">Industry</th>
              <th className="px-6 py-3 font-medium text-right">ARR</th>
              <th className="px-6 py-3 font-medium text-center">Health</th>
              <th className="px-6 py-3 font-medium text-right">Usage Trend</th>
              <th className="px-6 py-3 font-medium text-right">NPS</th>
              <th className="px-6 py-3 font-medium text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/50">
            {accounts.map((a) => (
              <tr key={a.id} className="hover:bg-gray-800/40 transition-colors">
                <td className="px-6 py-3">
                  <Link
                    to={`/account/${encodeURIComponent(a.name)}`}
                    className="font-medium text-indigo-400 hover:text-indigo-300"
                  >
                    {a.name}
                  </Link>
                </td>
                <td className="px-6 py-3 text-gray-400">{a.industry}</td>
                <td className="px-6 py-3 text-right text-gray-300">
                  {formatCurrency(a.arr)}
                </td>
                <td className="px-6 py-3 text-center">
                  <span
                    className={`font-mono text-xs font-bold ${
                      a.healthScore >= 70
                        ? "text-emerald-400"
                        : a.healthScore >= 45
                        ? "text-amber-400"
                        : "text-red-400"
                    }`}
                  >
                    {a.healthScore}
                  </span>
                </td>
                <td
                  className={`px-6 py-3 text-right font-mono text-xs ${
                    a.usageTrend > 0
                      ? "text-emerald-400"
                      : a.usageTrend < 0
                      ? "text-red-400"
                      : "text-gray-500"
                  }`}
                >
                  {a.usageTrend > 0 ? "+" : ""}
                  {a.usageTrend}%
                </td>
                <td className="px-6 py-3 text-right text-gray-400">
                  {a.npsScore}
                </td>
                <td className="px-6 py-3 text-center">
                  <HealthBadge status={a.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Overview page
// ---------------------------------------------------------------------------

export default function Overview() {
  const [accounts, setAccounts] = useState<Account[]>(MOCK_ACCOUNTS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchAccounts() {
      try {
        const result = await executeSQL(`
          SELECT account_name, industry, arr, licensed_seats, seat_utilization_pct,
                 avg_sentiment, competitor_mentioned, expansion_signal, typical_frustration,
                 current_ae, ae_changed_recently, pipeline_amount, nps_score,
                 total_features_used, power_features_used, feature_breadth_pct,
                 avg_discount_pct, overdue_invoices, usage_trend_wow_pct
          FROM MARTS.MART_ACCOUNT_HEALTH
          ORDER BY arr DESC
        `);

        if (!cancelled) {
          const mapped = result.rows.map(mapRowToAccount);
          setAccounts(mapped);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to fetch accounts from Snowflake:", err);
          setError(
            err instanceof Error ? err.message : "Failed to load live data"
          );
          // Keep mock data as fallback — already in state
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchAccounts();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Portfolio Overview</h1>
        <p className="mt-1 text-sm text-gray-500">
          DigitalNativeCo account health at a glance
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-700/50 bg-amber-900/20 px-4 py-3 text-sm text-amber-300">
          <strong>Warning:</strong> Could not load live data from Snowflake.
          Showing mock data.{" "}
          <span className="text-amber-500 text-xs block mt-1">{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-sm text-gray-500 animate-pulse">
            Loading accounts from Snowflake...
          </div>
        </div>
      ) : (
        <>
          <SummaryCards accounts={accounts} />
          <RiskHeatmap accounts={accounts} />
          <AccountTable accounts={accounts} />
        </>
      )}
    </div>
  );
}
