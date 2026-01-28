"use client";

import { VelocityReport, TrendVelocityAlert, AlertSeverity } from "@/types";

interface VelocityAlertsProps {
  velocity: VelocityReport;
}

/**
 * Velocity alerts panel with trading terminal aesthetics.
 * Displays anomaly alerts like market alerts in a trading app.
 */
export function VelocityAlerts({ velocity }: VelocityAlertsProps) {
  const { alerts, alert_count, warning_count, total_alerts } = velocity;

  // Sort by severity
  const severityOrder: Record<AlertSeverity, number> = {
    alert: 0,
    warning: 1,
    notable: 2,
    none: 3,
  };

  const sortedAlerts = [...alerts].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Velocity Alerts
            </p>
            <p className="text-xs text-white/30 mt-0.5">Anomaly detection (z-score)</p>
          </div>
          <div className="flex items-center gap-2">
            {alert_count > 0 && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-500/20 text-red-400 border border-red-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                {alert_count}
              </span>
            )}
            {warning_count > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-500/20 text-amber-400 border border-amber-500/20">
                {warning_count}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Alerts list or empty state */}
      {total_alerts === 0 ? (
        <div className="p-6 text-center">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/10 mb-3">
            <span className="text-emerald-400 text-lg">✓</span>
          </div>
          <p className="text-sm text-white/60">All metrics within normal range</p>
          <p className="text-[10px] text-white/30 mt-1">No anomalies detected (|z| &lt; 2.0)</p>
        </div>
      ) : (
        <div className="divide-y divide-white/[0.04] max-h-80 overflow-y-auto">
          {sortedAlerts.map((alert) => (
            <AlertRow key={alert.alert_id} alert={alert} />
          ))}
        </div>
      )}

      {/* Footer with velocity summary */}
      <div className="p-3 border-t border-white/[0.04]">
        <div className="flex justify-center gap-4">
          {velocity.metrics.slice(0, 4).map((metric) => (
            <div key={metric.metric_name} className="text-[9px] text-center min-w-[50px]">
              <p className="text-white/30 truncate">{formatMetricName(metric.metric_name)}</p>
              <p className={`tabular-nums font-medium ${getZScoreColor(metric.velocity_zscore)}`}>
                {metric.velocity_zscore >= 0 ? "+" : ""}{metric.velocity_zscore.toFixed(1)}σ
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface AlertRowProps {
  alert: TrendVelocityAlert;
}

function AlertRow({ alert }: AlertRowProps) {
  const config = {
    alert: {
      bg: "bg-red-500/[0.05]",
      border: "border-l-red-500",
      icon: "●",
      iconColor: "text-red-400",
      badge: "bg-red-500/20 text-red-400",
    },
    warning: {
      bg: "bg-amber-500/[0.03]",
      border: "border-l-amber-500",
      icon: "◐",
      iconColor: "text-amber-400",
      badge: "bg-amber-500/20 text-amber-400",
    },
    notable: {
      bg: "",
      border: "border-l-blue-500/50",
      icon: "○",
      iconColor: "text-blue-400",
      badge: "bg-blue-500/20 text-blue-400",
    },
    none: {
      bg: "",
      border: "border-l-white/10",
      icon: "·",
      iconColor: "text-white/30",
      badge: "bg-white/10 text-white/40",
    },
  }[alert.severity];

  const directionColor = alert.direction === "rising" ? "text-emerald-400" : "text-red-400";

  return (
    <div className={`px-4 py-3 border-l-2 ${config.border} ${config.bg} hover:bg-white/[0.02] transition-colors`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Header with severity and z-score */}
          <div className="flex items-center gap-2">
            <span className={`${config.iconColor} text-sm`}>{config.icon}</span>
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${config.badge}`}>
              {alert.severity.toUpperCase()}
            </span>
            {alert.category && (
              <span className="text-[10px] text-white/40 capitalize">
                {alert.category}
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-xs text-white/70 mt-1.5 leading-relaxed">
            {alert.description}
          </p>

          {/* Stats row */}
          <div className="flex items-center gap-3 mt-2 text-[10px] text-white/40">
            <span className={`tabular-nums ${directionColor}`}>
              z = {alert.z_score >= 0 ? "+" : ""}{alert.z_score.toFixed(2)}
            </span>
            <span className="text-white/20">|</span>
            <span className="tabular-nums">P{alert.percentile.toFixed(0)}</span>
            <span className="text-white/20">|</span>
            <span className="tabular-nums">
              {alert.current_value.toFixed(2)} vs {alert.expected_value.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Direction indicator */}
        <div className={`text-2xl ${directionColor}`}>
          {alert.direction === "rising" ? "↗" : "↘"}
        </div>
      </div>
    </div>
  );
}

function formatMetricName(name: string): string {
  return name
    .replace("_zscore_sum", "")
    .replace("composite_score", "Overall")
    .charAt(0).toUpperCase() + name.replace("_zscore_sum", "").replace("composite_score", "overall").slice(1);
}

function getZScoreColor(z: number): string {
  const absZ = Math.abs(z);
  if (absZ >= 2.0) return z > 0 ? "text-emerald-400" : "text-red-400";
  if (absZ >= 1.5) return z > 0 ? "text-emerald-400/70" : "text-red-400/70";
  return "text-white/50";
}