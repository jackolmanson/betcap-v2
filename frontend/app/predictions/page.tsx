import { getPicksForDate, getLatestPickDate } from "@/lib/db";
import MatchupCard from "@/components/MatchupCard";

export const dynamic = "force-dynamic";

function formatDate(date: Date | string): string {
  // Accepts either a game_time Date or a fallback YYYY-MM-DD string
  const d = typeof date === "string"
    ? (() => { const [y, m, day] = date.split("-").map(Number); return new Date(y, m - 1, day); })()
    : new Date(date);
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "America/New_York",
  });
}

export default async function PredictionsPage() {
  const date = await getLatestPickDate();
  const picks = date ? await getPicksForDate(date) : [];

  // Derive the display date from the actual game times when available
  const displayDate = picks[0]?.game_time
    ? formatDate(picks[0].game_time)
    : date
    ? formatDate(date)
    : null;

  return (
    <main className="max-w-6xl mx-auto px-6 sm:px-10 py-8 lg:py-12">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-1" style={{ color: "var(--text)" }}>
          Men&apos;s College Basketball Predictions
        </h1>
        {displayDate && (
          <p className="text-sm sm:text-base mt-1" style={{ color: "var(--text-muted)" }}>
            {displayDate}
          </p>
        )}
        <hr className="mt-4" style={{ borderColor: "var(--border)" }} />
      </div>

      {!date || picks.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-lg font-semibold mb-2" style={{ color: "var(--text)" }}>Roadblock!</p>
          <p className="text-sm sm:text-base" style={{ color: "var(--text-muted)" }}>
            There was either an internal server error or there are no NCAAB games today. Come back later!
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm font-medium mb-5" style={{ color: "var(--text-muted)" }}>
            {picks.length} upcoming game{picks.length !== 1 ? "s" : ""}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
            {picks.map((pick) => (
              <MatchupCard key={pick.id} pick={pick} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
