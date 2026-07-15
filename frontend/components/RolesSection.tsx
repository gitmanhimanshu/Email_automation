import Reveal from "@/components/Reveal";
import { ROLES } from "@/lib/site";

/** Setu asks what you do, once, and adapts what rides along with each email. */
export default function RolesSection() {
  return (
    <section className="mt-24">
      <Reveal>
        <h2 className="text-3xl font-semibold tracking-tight text-center">
          Not just for job seekers
        </h2>
        <p className="mt-4 text-[var(--text-secondary)] max-w-2xl mx-auto text-center leading-relaxed">
          Setu asks what you do, once. The machinery underneath is identical —
          your Gmail, your assistant, your approval — but what attaches to the
          email changes, and so does what a good email even looks like.
        </p>
      </Reveal>

      <div className="mt-10 grid gap-4 sm:grid-cols-3">
        {ROLES.map((role, i) => (
          <Reveal key={role.id} delay={i * 0.05}>
            <div className="h-full rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <h3 className="font-semibold">{role.label}</h3>
              <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                {role.body}
              </p>
              <p className="mt-5 pt-4 border-t border-[var(--border)] text-xs text-[var(--text-muted)]">
                Attaches{" "}
                <span className="font-medium text-[var(--text-secondary)]">
                  {role.link}
                </span>{" "}
                — {role.required ? "required" : "optional"}
              </p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.1}>
        <p className="mt-6 text-sm text-[var(--text-muted)] text-center max-w-2xl mx-auto leading-relaxed">
          Switch any time. A job seeker who gets hired and starts recruiting just
          says so, and Setu adjusts.
        </p>
      </Reveal>
    </section>
  );
}
