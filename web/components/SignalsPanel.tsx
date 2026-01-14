import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Signal, SignalType } from "@/types";

interface SignalsPanelProps {
  signals: Signal[];
}

function getSignalIcon(type: SignalType): string {
  switch (type) {
    case "high_engagement": return "🔥";
    case "emerging_topic": return "🆕";
    case "intensity_spike": return "⚡";
    case "volume_spike": return "📈";
    default: return "📍";
  }
}

function getSignalLabel(type: SignalType): string {
  switch (type) {
    case "high_engagement": return "High Engagement";
    case "emerging_topic": return "Emerging Topic";
    case "intensity_spike": return "Intensity Spike";
    case "volume_spike": return "Volume Spike";
    default: return type;
  }
}

function getUrgencyColor(urgency: string): string {
  switch (urgency) {
    case "high": return "bg-red-500/20 text-red-400 border-red-500/30";
    case "medium": return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "low": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  }
}

export function SignalsPanel({ signals }: SignalsPanelProps) {
  if (!signals || signals.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {signals.map((signal, i) => (
        <Card key={i} className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getSignalIcon(signal.signal_type)}</span>
                <CardTitle className="text-base text-white">{signal.title}</CardTitle>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <Badge variant="outline" className="text-xs">
                  {getSignalLabel(signal.signal_type)}
                </Badge>
                <Badge
                  variant="outline"
                  className={`text-xs ${getUrgencyColor(signal.urgency)}`}
                >
                  {signal.urgency}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">{signal.description}</p>
            {signal.related_quotes.length > 0 && (
              <div className="space-y-1">
                {signal.related_quotes.slice(0, 2).map((quote, j) => (
                  <p key={j} className="text-xs text-zinc-400 italic pl-3 border-l border-zinc-700">
                    {quote}
                  </p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}