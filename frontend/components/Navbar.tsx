export default function Navbar() {
  return (
    <nav style={{ background: "var(--navbar)" }} className="w-full px-6 py-3 flex items-center justify-between">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <BasketballIcon />
        <span className="text-white font-semibold text-lg tracking-wide">
          Betquity Capital
        </span>
      </div>

      {/* Nav links */}
      <div className="flex items-center gap-6">
        {["About", "Predictions", "Performance", "Support"].map((link) => (
          <a
            key={link}
            href="#"
            className="text-white text-sm opacity-80 hover:opacity-100 transition-opacity no-underline"
            style={{ textDecoration: "none" }}
          >
            {link}
          </a>
        ))}
      </div>
    </nav>
  );
}

function BasketballIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="14" cy="14" r="13" stroke="white" strokeWidth="1.5" fill="none" />
      <path d="M1 14h26" stroke="white" strokeWidth="1.5" />
      <path d="M14 1v26" stroke="white" strokeWidth="1.5" />
      <path d="M4 5.5C7 9 7 19 4 22.5" stroke="white" strokeWidth="1.5" fill="none" />
      <path d="M24 5.5C21 9 21 19 24 22.5" stroke="white" strokeWidth="1.5" fill="none" />
    </svg>
  );
}
