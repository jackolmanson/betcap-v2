import { getPicksForDate, getLatestPickDate } from "@/lib/db";
import MatchupCard from "@/components/MatchupCard";

export const dynamic = "force-dynamic";

function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export default async function HomePage() {
  const date = await getLatestPickDate();
  const picks = date ? await getPicksForDate(date) : [];

  return (
    <main className="max-w-5xl mx-auto px-6 py-8">
      {/* Page header — matches existing site's predictions page */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>
          Men&apos;s College Basketball Predictions
        </h1>
        {date && (
          <p className="text-sm italic" style={{ color: "var(--text-muted)" }}>
            {formatDate(date)}
          </p>
        )}
        <hr className="mt-4" style={{ borderColor: "var(--border)" }} />
      </div>

      {!date || picks.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-lg font-semibold mb-2" style={{ color: "var(--text)" }}>Roadblock!</p>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            There was either an internal server error or there are no NCAAB games today. Come back later!
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
            {picks.length} game{picks.length !== 1 ? "s" : ""} today
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {picks.map((pick) => (
              <MatchupCard key={pick.id} pick={pick} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
