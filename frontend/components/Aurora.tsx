/* Slow drifting blobs behind the hero, in the logo's own blue→violet gradient.
   Pure decoration: aria-hidden, pointer-events-none, and it sits behind content
   so it can never intercept a click. Motion is CSS-only and honours
   prefers-reduced-motion via the global reset in globals.css. */
export default function Aurora() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
    >
      <span className="aurora-blob aurora-1" />
      <span className="aurora-blob aurora-2" />
      <span className="aurora-blob aurora-3" />

      {/* The wordmark, oversized and drifting behind everything. Decorative
          only — the real name is in the <h1>, so screen readers and search
          engines read it there, not here. */}
      <span className="aurora-word aurora-word-hi">सेतु</span>
      <span className="aurora-word aurora-word-en">SETU</span>

      <div className="aurora-veil" />
    </div>
  );
}
