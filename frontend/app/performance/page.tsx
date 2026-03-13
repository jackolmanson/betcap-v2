import { getAllPicksWithResults } from "@/lib/db";
import PerformanceClient from "@/components/PerformanceClient";

export const dynamic = "force-dynamic";

export default async function PerformancePage() {
  const picks = await getAllPicksWithResults();
  return <PerformanceClient picks={picks} />;
}
