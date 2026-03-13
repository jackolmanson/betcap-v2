"use client";

import { useState } from "react";

const NAV_LINKS = [
  { label: "About", href: "/about" },
  { label: "Predictions", href: "/predictions" },
  { label: "Performance", href: "/performance" },
  { label: "Support", href: "#" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav style={{ background: "var(--navbar)" }} className="w-full px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-3" style={{ textDecoration: "none" }}>
          <BasketballIcon />
          <span className="text-white font-semibold text-lg tracking-wide">
            Betquity Capital
          </span>
        </a>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              className="text-white text-sm opacity-80 hover:opacity-100 transition-opacity"
              style={{ textDecoration: "none" }}
            >
              {label}
            </a>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          <span className={`block w-6 h-0.5 bg-white transition-transform duration-200 ${open ? "rotate-45 translate-y-2" : ""}`} />
          <span className={`block w-6 h-0.5 bg-white transition-opacity duration-200 ${open ? "opacity-0" : ""}`} />
          <span className={`block w-6 h-0.5 bg-white transition-transform duration-200 ${open ? "-rotate-45 -translate-y-2" : ""}`} />
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden pt-4 pb-2 flex flex-col gap-4">
          {NAV_LINKS.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              onClick={() => setOpen(false)}
              className="text-white text-base opacity-80 hover:opacity-100 transition-opacity py-1"
              style={{ textDecoration: "none" }}
            >
              {label}
            </a>
          ))}
        </div>
      )}
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
