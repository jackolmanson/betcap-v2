import { getUpcomingPicks } from "@/lib/db";
import MatchupCard from "@/components/MatchupCard";
import ScoreTodayButton from "@/components/ScoreTodayButton";

export const dynamic = "force-dynamic";

function formatDate(isoDate: string): string {
  return new Date(isoDate + "T12:00:00Z").toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "America/New_York",
  });
}

export default async function PredictionsPage() {
  const picks = await getUpcomingPicks();

  const byDate: Record<string, typeof picks> = {};
  for (const pick of picks) {
    const d = pick.date!;
    (byDate[d] ??= []).push(pick);
  }
  const dates = Object.keys(byDate).sort();
  const multiDay = dates.length > 1;

  return (
    <main className="max-w-6xl mx-auto px-6 sm:px-10 py-8 lg:py-12">
      <div className="mb-8">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: "var(--text)" }}>
            Men&apos;s College Basketball Predictions
          </h1>
          <ScoreTodayButton />
        </div>
        {!multiDay && dates[0] && (
          <p className="text-sm sm:text-base mt-1" style={{ color: "var(--text-muted)" }}>
            {formatDate(dates[0])}
          </p>
        )}
        <hr className="mt-4" style={{ borderColor: "var(--border)" }} />
      </div>

      {picks.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-lg font-semibold mb-2" style={{ color: "var(--text)" }}>Roadblock!</p>
          <p className="text-sm sm:text-base" style={{ color: "var(--text-muted)" }}>
            There was either an internal server error or there are no NCAAB games today. Come back later!
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm font-medium mb-5" style={{ color: "var(--text-muted)" }}>
            {picks.length} game{picks.length !== 1 ? "s" : ""}
          </p>
          {dates.map((d) => (
            <div key={d} className="mb-10">
              {multiDay && (
                <h2 className="text-base font-bold mb-4" style={{ color: "var(--text)" }}>
                  {formatDate(d)}
                </h2>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
                {byDate[d].map((pick) => (
                  <MatchupCard key={pick.id} pick={pick} />
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </main>
  );
}
