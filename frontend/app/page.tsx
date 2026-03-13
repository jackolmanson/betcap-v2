export default function HomePage() {
  return (
    <main
      className="min-h-[calc(100vh-56px)] flex items-center"
      style={{ background: "var(--bg)" }}
    >
      <div className="max-w-6xl mx-auto px-6 sm:px-10 py-16 w-full flex flex-col lg:flex-row items-center gap-12 lg:gap-16">

        {/* Copy */}
        <div className="flex-1 text-center lg:text-left">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight mb-6">
            Welcome to the Sports Betting Revolution
          </h1>
          <p
            className="text-base sm:text-lg leading-relaxed mb-8 max-w-xl mx-auto lg:mx-0"
            style={{ color: "var(--text-muted)" }}
          >
            Betquity Capital (est. 2023) strives to be the globe&apos;s leading college
            basketball sharp and generate superior long-term returns for sports bettors
            across the world. We do not consider our picks to be gambling, but rather an
            investment de-risked through tried and tested artificial intelligence modeling.
          </p>
          <div className="flex items-center justify-center lg:justify-start gap-4">
            <a
              href="/about"
              className="px-7 py-3 rounded-lg font-semibold text-sm sm:text-base text-white transition-opacity hover:opacity-90"
              style={{ background: "var(--accent)" }}
            >
              Learn More
            </a>
            <a
              href="/predictions"
              className="px-7 py-3 rounded-lg font-semibold text-sm sm:text-base transition-opacity hover:opacity-80"
              style={{
                background: "transparent",
                border: "2px solid var(--text)",
                color: "var(--text)",
              }}
            >
              See the Picks
            </a>
          </div>
        </div>

        {/* Court image */}
        <div
          className="w-full sm:w-3/4 lg:w-[420px] xl:w-[480px] h-60 sm:h-72 lg:h-80 flex-shrink-0 rounded-2xl overflow-hidden"
          style={{ border: "1px solid var(--border)" }}
        >
          <img src="/court.png" alt="Basketball court" className="w-full h-full object-cover" />
        </div>

      </div>
    </main>
  );
}
