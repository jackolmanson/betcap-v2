import TeamPhoto from "@/components/TeamPhoto";

export default function AboutPage() {
  return (
    <main className="max-w-5xl mx-auto px-6 py-12">

      {/* ── Section 1: We Build Winners ── */}
      <section className="flex items-center gap-12 mb-16">
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-4" style={{ color: "var(--text)" }}>
            We Build Winners.
          </h1>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
            We understand the challenge of investing money into spread bets – a theoretical
            50/50 coin flip must be predicted correctly over 52.38% of the time to overcome
            the vig and generate profits. We believe our proprietary machine learning spread
            model gives us the edge to do just this: we have fed our model 20 years of game
            data to discover the most important variables and calculations to make an educated
            prediction on what side of the market spread to take.
          </p>
        </div>
        <img src="/winner.png" alt="We Build Winners" className="w-44 h-44 flex-shrink-0 object-contain" />
      </section>

      <hr className="mb-16" style={{ borderColor: "var(--border)" }} />

      {/* ── Section 2: Our Investment Thesis ── */}
      <section className="flex items-center gap-12 mb-16">
        <img src="/story.png" alt="Investment Thesis" className="w-44 h-44 flex-shrink-0 object-contain" />
        <div className="flex-1">
          <h2 className="text-2xl font-bold mb-4" style={{ color: "var(--text)" }}>
            Our Investment Thesis
          </h2>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
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
        <h2 className="text-2xl font-bold mb-4" style={{ color: "var(--text)" }}>
          Our Story
        </h2>
        <p className="text-sm leading-relaxed mb-10" style={{ color: "var(--text-muted)" }}>
          This model was initially created for personal use in Spring 2021 to improve
          Jack&apos;s March Madness brackets and overall betting performance. Multi-season
          success indicated that sustained performance was possible and that these picks
          could provide value to the world.
        </p>

        <div className="flex flex-col gap-4">
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

function IllustrationBox({ emoji }: { emoji: string }) {
  return (
    <div
      className="w-44 h-44 flex-shrink-0 rounded-xl flex items-center justify-center text-7xl"
      style={{ background: "var(--card)", border: "1px solid var(--border)" }}
    >
      {emoji}
    </div>
  );
}

function TeamCard({
  photoSrc,
  initials,
  name,
  role,
  bio,
  email,
  linkedin,
  favTeam,
  bestOdds,
  favMemory,
}: {
  photoSrc: string;
  initials: string;
  name: string;
  role: string;
  bio: string;
  email?: string;
  linkedin?: string;
  favTeam: string;
  bestOdds: string;
  favMemory: string;
}) {
  return (
    <div
      className="flex rounded-lg overflow-hidden"
      style={{ border: "1px solid var(--border)", background: "var(--card)" }}
    >
      {/* Photo */}
      <div
        className="w-36 flex-shrink-0 flex items-center justify-center overflow-hidden"
        style={{ background: "var(--bg)", minHeight: "160px" }}
      >
        <TeamPhoto src={photoSrc} initials={initials} name={name} />
      </div>

      {/* Bio */}
      <div className="flex-1 px-6 py-5">
        <p className="font-bold text-base mb-0.5" style={{ color: "var(--text)" }}>{name}</p>
        <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>{role}</p>
        <p className="text-xs leading-relaxed mb-3" style={{ color: "var(--text-muted)" }}>{bio}</p>
        {(email || linkedin) && (
          <div className="flex gap-3 text-xs">
            {email && (
              <a href={email} style={{ color: "var(--accent)" }}>
                Email
              </a>
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
        className="w-56 flex-shrink-0 px-6 py-5 flex flex-col gap-3"
        style={{ borderLeft: "1px solid var(--border)" }}
      >
        <Stat label="Favorite Sports Team:" value={favTeam} />
        <Stat label="Best Odds Hit:" value={bestOdds} />
        <Stat label="Favorite Sports Memory:" value={favMemory} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>{label}</p>
      <p className="text-xs" style={{ color: "var(--text)" }}>{value}</p>
    </div>
  );
}

