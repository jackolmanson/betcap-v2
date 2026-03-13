import TeamPhoto from "@/components/TeamPhoto";

export default function AboutPage() {
  return (
    <main className="max-w-5xl mx-auto px-6 sm:px-10 py-12 lg:py-16">

      {/* ── Section 1: We Build Winners ── */}
      <section className="flex flex-col lg:flex-row items-center gap-8 lg:gap-14 mb-16">
        <div className="flex-1 text-center lg:text-left">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4" style={{ color: "var(--text)" }}>
            We Build Winners.
          </h1>
          <p className="text-sm sm:text-base leading-relaxed" style={{ color: "var(--text-muted)" }}>
            We understand the challenge of investing money into spread bets – a theoretical
            50/50 coin flip must be predicted correctly over 52.38% of the time to overcome
            the vig and generate profits. We believe our proprietary machine learning spread
            model gives us the edge to do just this: we have fed our model 20 years of game
            data to discover the most important variables and calculations to make an educated
            prediction on what side of the market spread to take.
          </p>
        </div>
        <img
          src="/winner.png"
          alt="We Build Winners"
          className="w-32 h-32 sm:w-40 sm:h-40 lg:w-48 lg:h-48 flex-shrink-0 object-contain"
        />
      </section>

      <hr className="mb-16" style={{ borderColor: "var(--border)" }} />

      {/* ── Section 2: Our Investment Thesis ── */}
      <section className="flex flex-col-reverse lg:flex-row items-center gap-8 lg:gap-14 mb-16">
        <img
          src="/story.png"
          alt="Investment Thesis"
          className="w-32 h-32 sm:w-40 sm:h-40 lg:w-48 lg:h-48 flex-shrink-0 object-contain"
        />
        <div className="flex-1 text-center lg:text-left">
          <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold mb-4" style={{ color: "var(--text)" }}>
            Our Investment Thesis
          </h2>
          <p className="text-sm sm:text-base leading-relaxed" style={{ color: "var(--text-muted)" }}>
            We believe in hands-off investing – we trust the model we have trained and tested
            to make each decision. Analyzing the selections over time, we can tell the model
            has a few hypotheses on how best to invest capital. The first is that road
            underdogs are under indexed in the public eye. The second is that conference games
            tend to be closer games.
          </p>
        </div>
      </section>

      <hr className="mb-12" style={{ borderColor: "var(--border)" }} />

      {/* ── Section 3: Our Story ── */}
      <section>
        <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold mb-4" style={{ color: "var(--text)" }}>
          Our Story
        </h2>
        <p className="text-sm sm:text-base leading-relaxed mb-10" style={{ color: "var(--text-muted)" }}>
          This model was initially created for personal use in Spring 2021 to improve
          Jack&apos;s March Madness brackets and overall betting performance. Multi-season
          success indicated that sustained performance was possible and that these picks
          could provide value to the world.
        </p>

        <div className="flex flex-col gap-6">
          <TeamCard
            photoSrc="/jack.jpg"
            initials="JO"
            name="Jack Olmanson"
            role="Founder"
            bio="Jack currently works in the financial services sector. He also has experience in management consulting and high-growth startups. He graduated from the University of Notre Dame in 2021 with a B.S. in Computer Science."
            linkedin="https://www.linkedin.com/in/jack-olmanson/"
            favTeam="Any Minnesota team, Notre Dame"
            bestOdds="+6800 CFB Parlay"
            favMemory="The Minneapolis Miracle"
          />
          <TeamCard
            photoSrc="/machine.jpeg"
            initials="ML"
            name="Chives (The Model)"
            role="Data Analyst"
            bio="Chives currently works as a data analyst at Betquity Capital. It aspires to someday become sentient and serve as the GM for the Orlando Magic."
            favTeam="All Men's College Basketball Teams"
            bestOdds="-110"
            favMemory="Pete Weber winning his fifth U.S. Open with a championship-clinching strike"
          />
        </div>
      </section>

    </main>
  );
}

function TeamCard({
  photoSrc, initials, name, role, bio, email, linkedin,
  favTeam, bestOdds, favMemory,
}: {
  photoSrc: string; initials: string; name: string; role: string; bio: string;
  email?: string; linkedin?: string; favTeam: string; bestOdds: string; favMemory: string;
}) {
  return (
    <div
      className="flex flex-col sm:flex-row rounded-xl overflow-hidden"
      style={{ border: "1px solid var(--border)", background: "var(--card)" }}
    >
      {/* Photo */}
      <div
        className="flex items-center justify-center overflow-hidden sm:w-40 sm:flex-shrink-0"
        style={{ background: "var(--bg)", minHeight: "180px" }}
      >
        <TeamPhoto src={photoSrc} initials={initials} name={name} />
      </div>

      {/* Bio */}
      <div className="flex-1 px-6 py-6">
        <p className="font-bold text-lg mb-0.5" style={{ color: "var(--text)" }}>{name}</p>
        <p className="text-sm mb-3 font-medium" style={{ color: "var(--accent)" }}>{role}</p>
        <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-muted)" }}>{bio}</p>
        {(email || linkedin) && (
          <div className="flex gap-4 text-sm">
            {email && (
              <a href={email} style={{ color: "var(--accent)" }}>Email</a>
            )}
            {linkedin && (
              <a href={linkedin} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)" }}>
                LinkedIn
              </a>
            )}
          </div>
        )}
      </div>

      {/* Stats */}
      <div
        className="px-6 py-6 flex flex-col gap-4 sm:w-56 sm:flex-shrink-0"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <Stat label="Favorite Sports Team" value={favTeam} />
        <Stat label="Best Odds Hit" value={bestOdds} />
        <Stat label="Favorite Sports Memory" value={favMemory} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide mb-0.5" style={{ color: "var(--text-muted)" }}>{label}</p>
      <p className="text-sm" style={{ color: "var(--text)" }}>{value}</p>
    </div>
  );
}
