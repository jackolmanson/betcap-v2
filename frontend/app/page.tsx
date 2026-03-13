export default function HomePage() {
  return (
    <main
      className="min-h-screen flex items-center"
      style={{ background: "var(--bg)" }}
    >
      <div className="max-w-5xl mx-auto px-6 w-full flex items-center gap-12">

        {/* Left — copy */}
        <div className="flex-1">
          <h1
            className="text-5xl font-bold leading-tight mb-8"
            style={{ color: "var(--text)" }}
          >
            Welcome to the Sports Betting Revolution
          </h1>
          <p
            className="text-base leading-relaxed mb-10 max-w-lg"
            style={{ color: "var(--text-muted)" }}
          >
            Betquity Capital (est. 2023) strives to be the globe&apos;s leading college
            basketball sharp and generate superior long-term returns for sports bettors
            across the world. We do not consider our picks to be gambling, but rather an
            investment de-risked through tried and tested artificial intelligence modeling.
          </p>
          <div className="flex items-center gap-4">
            <a
              href="/about"
              className="px-6 py-3 rounded font-semibold text-sm text-white transition-opacity hover:opacity-90"
              style={{ background: "var(--accent)" }}
            >
              Learn More
            </a>
            <a
              href="/predictions"
              className="px-6 py-3 rounded font-semibold text-sm transition-opacity hover:opacity-80"
              style={{
                background: "transparent",
                border: "1px solid var(--text)",
                color: "var(--text)",
              }}
            >
              See the Picks
            </a>
          </div>
        </div>

        {/* Right — court image */}
        <div className="hidden md:flex flex-shrink-0 w-96 h-72 rounded-2xl overflow-hidden"
          style={{ border: "1px solid var(--border)" }}
        >
          <img src="/images/court.png" alt="Basketball court" className="w-full h-full object-cover" />
        </div>

      </div>
    </main>
  );
}
