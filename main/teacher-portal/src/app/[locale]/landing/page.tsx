"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { LanguageSwitcher } from "@/components/language-switcher";
import {
  Mic,
  Cpu,
  BrainCircuit,
  AudioLines,
  BookOpen,
  Fingerprint,
  Database,
  ShieldCheck,
  GraduationCap,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

const HOW_IT_WORKS = [
  { icon: Mic, color: "bg-indigo-500", key: "1" },
  { icon: Cpu, color: "bg-rose-500", key: "2" },
  { icon: BrainCircuit, color: "bg-amber-500", key: "3" },
  { icon: AudioLines, color: "bg-emerald-500", key: "4" },
] as const;

const FEATURES = [
  { icon: BookOpen, key: "1" },
  { icon: Fingerprint, key: "2" },
  { icon: Database, key: "3" },
] as const;

const TRUST_CARDS = [
  { icon: ShieldCheck, key: "1" },
  { icon: GraduationCap, key: "2" },
] as const;

const NAV_LINKS = ["howItWorks", "features", "trust", "cta"] as const;

export default function LandingPage() {
  const t = useTranslations("Landing");

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Navbar ── */}
      <nav aria-label="Landing navigation" className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <span className="text-xl font-bold tracking-tight">
            <span className="text-primary">Mekong</span>AI
          </span>
          <div className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex">
            {NAV_LINKS.map((id) => (
              <a key={id} href={`#${id}`} className="transition-colors hover:text-foreground">
                {t(`nav${id.charAt(0).toUpperCase() + id.slice(1)}`)}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <Link
              href="/login"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              {t("heroCta")}
            </Link>
          </div>
        </div>
      </nav>

      <main>
        {/* ── Hero ── */}
        <section className="relative overflow-hidden pb-20 pt-24 md:pt-32">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(79,70,229,0.10),transparent)]" />
          <div className="mx-auto max-w-4xl px-6 text-center">
            <span className="mb-6 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
              {t("heroTag")}
            </span>
            <h1 className="mt-6 text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
              {t("heroTitle")}
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
              {t("heroDescription")}
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl"
              >
                {t("heroCta")}
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#howItWorks"
                className="inline-flex items-center gap-2 rounded-lg border border-border px-6 py-3 font-semibold transition-colors hover:bg-accent"
              >
                {t("heroSecondaryCta")}
              </a>
            </div>
          </div>
        </section>

        {/* ── How It Works ── */}
        <section id="howItWorks" className="bg-muted/30 py-20">
          <div className="mx-auto max-w-5xl px-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                {t("howTitle")}
              </h2>
              <p className="mx-auto mt-3 max-w-2xl text-base text-muted-foreground">
                {t("howSubtitle")}
              </p>
            </div>
            <div className="mt-14 grid grid-cols-2 gap-8 md:grid-cols-4">
              {HOW_IT_WORKS.map(({ icon: Icon, color, key }) => (
                <div key={key} className="flex flex-col items-center text-center">
                  <div className={`mb-4 flex h-16 w-16 items-center justify-center rounded-2xl ${color} text-white shadow-md`}>
                    <Icon className="h-7 w-7" />
                  </div>
                  <h3 className="text-sm font-semibold">{t(`how${key}Title`)}</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                    {t(`how${key}Desc`)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features ── */}
        <section id="features" className="py-20">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="text-center text-3xl font-bold tracking-tight sm:text-4xl">
              {t("featuresTitle")}
            </h2>
            <div className="mt-14 grid gap-6 md:grid-cols-3">
              {FEATURES.map(({ icon: Icon, key }) => (
                <div
                  key={key}
                  className="group rounded-2xl border border-border/60 bg-card p-7 transition-all hover:border-primary/30 hover:shadow-lg"
                >
                  <div className="mb-5 inline-flex rounded-xl bg-primary/10 p-3 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold">{t(`feature${key}Title`)}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {t(`feature${key}Desc`)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Trust (blue gradient) ── */}
        <section id="trust" className="relative overflow-hidden bg-primary py-20 text-primary-foreground">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(255,255,255,0.08),transparent)]" />
          <div className="relative mx-auto max-w-4xl px-6 text-center">
            <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full bg-white/15">
              <ShieldCheck className="h-7 w-7" />
            </div>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              {t("trustTitle")}
            </h2>
            <div className="mt-10 grid gap-6 sm:grid-cols-2">
              {TRUST_CARDS.map(({ icon: Icon, key }) => (
                <div
                  key={key}
                  className="rounded-2xl bg-white/10 p-6 text-left backdrop-blur-sm"
                >
                  <div className="mb-3 inline-flex items-center gap-2 text-sm font-semibold">
                    <Icon className="h-4 w-4" />
                    {t(`trust${key}Title`)}
                  </div>
                  <p className="text-sm leading-relaxed text-primary-foreground/80">
                    {t(`trust${key}Desc`)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section id="cta" className="py-20">
          <div className="mx-auto max-w-3xl px-6">
            <div className="rounded-3xl bg-muted/60 px-8 py-14 text-center sm:px-14">
              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
                {t("ctaTitle")}
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-base text-muted-foreground">
                {t("ctaDescription")}
              </p>
              <div className="mt-8">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 rounded-full bg-primary px-8 py-3 font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90"
                >
                  {t("ctaButton")}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-border/50 bg-muted/30 py-12">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-10 sm:grid-cols-2 md:grid-cols-4">
            {/* Brand */}
            <div>
              <span className="text-lg font-bold">
                <span className="text-primary">Mekong</span>AI
              </span>
              <p className="mt-2 text-sm text-muted-foreground">
                {t("footerTagline")}
              </p>
            </div>
            {/* Products */}
            <div>
              <h4 className="mb-3 text-sm font-semibold">{t("footerProductsTitle")}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#howItWorks" className="transition-colors hover:text-foreground">{t("footerProduct1")}</a></li>
                <li><a href="#features" className="transition-colors hover:text-foreground">{t("footerProduct2")}</a></li>
                <li><a href="#trust" className="transition-colors hover:text-foreground">{t("footerProduct3")}</a></li>
              </ul>
            </div>
            {/* Support */}
            <div>
              <h4 className="mb-3 text-sm font-semibold">{t("footerSupportTitle")}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="https://github.com/mekongai" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 transition-colors hover:text-foreground">
                    <ExternalLink className="h-3 w-3" />
                    GitHub
                  </a>
                </li>
                <li><a href="#" className="transition-colors hover:text-foreground">{t("footerSupport1")}</a></li>
              </ul>
            </div>
            {/* Legal */}
            <div>
              <h4 className="mb-3 text-sm font-semibold">{t("footerLegalTitle")}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="transition-colors hover:text-foreground">{t("footerLegal1")}</a></li>
                <li><a href="#" className="transition-colors hover:text-foreground">{t("footerLegal2")}</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-10 border-t border-border/50 pt-6 text-center text-xs text-muted-foreground">
            {t("footerCopyright")}
          </div>
        </div>
      </footer>
    </div>
  );
}
