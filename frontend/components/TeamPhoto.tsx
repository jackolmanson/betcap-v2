"use client";
import { useState } from "react";

export default function TeamPhoto({ src, initials, name }: { src: string; initials: string; name: string }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <div
        className="w-full h-full flex items-center justify-center text-2xl font-bold"
        style={{ minHeight: "160px", color: "var(--text-muted)" }}
      >
        {initials}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={name}
      className="w-full h-full object-cover"
      style={{ minHeight: "160px" }}
      onError={() => setFailed(true)}
    />
  );
}
