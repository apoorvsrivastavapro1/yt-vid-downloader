import { useState } from "react";
import { Download, Link2, Loader2, Music, Play, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  fetchVideoInfo,
  getDownloadUrl,
  type FormatOption,
  type VideoInfo,
} from "@/lib/api";

type Tab = "mp4" | "mp3";

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoInfo | null>(null);
  const [tab, setTab] = useState<Tab>("mp4");

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await fetchVideoInfo(url.trim());
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const formats: FormatOption[] = result
    ? tab === "mp4"
      ? result.formats.mp4
      : result.formats.mp3
    : [];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-foreground">
              <Play className="h-4 w-4 fill-background text-background" />
            </div>
            <span className="text-base font-semibold tracking-tight">Loop</span>
          </div>
          <nav className="hidden gap-8 text-sm text-muted-foreground sm:flex">
            <a href="#how" className="transition-colors hover:text-foreground">
              How it works
            </a>
            <a href="#faq" className="transition-colors hover:text-foreground">
              FAQ
            </a>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 pb-24 pt-20">
        <section className="text-center">
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            YouTube videos,{" "}
            <span className="text-muted-foreground">downloaded simply.</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base text-muted-foreground">
            Paste a YouTube link, choose MP4 or MP3, and grab your file. No
            clutter, no ads.
          </p>
        </section>

        <form onSubmit={handleFetch} className="mt-12">
          <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-2 shadow-sm sm:flex-row">
            <div className="relative flex-1">
              <Link2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="h-12 border-0 bg-transparent pl-10 text-base shadow-none focus-visible:ring-0"
              />
            </div>
            <Button
              type="submit"
              size="lg"
              disabled={loading || !url.trim()}
              className="h-12 px-6"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Fetching
                </>
              ) : (
                "Get formats"
              )}
            </Button>
          </div>
          {error && (
            <p className="mt-3 text-center text-sm text-red-600">{error}</p>
          )}
          <p className="mt-3 text-center text-xs text-muted-foreground">
            By using Loop, you agree to download only content you have rights to.
          </p>
        </form>

        {result && (
          <section className="mt-10 overflow-hidden rounded-xl border border-border bg-card shadow-sm">
            <div className="flex gap-4 border-b border-border p-5">
              {result.thumbnail ? (
                <img
                  src={result.thumbnail}
                  alt=""
                  className="h-20 w-32 shrink-0 rounded-md object-cover"
                />
              ) : (
                <div className="flex h-20 w-32 shrink-0 items-center justify-center rounded-md bg-muted">
                  <Play className="h-6 w-6 text-muted-foreground" />
                </div>
              )}
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-base font-medium">{result.title}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {result.channel}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Duration {result.duration_formatted}
                </p>
              </div>
            </div>

            <div className="flex gap-1 border-b border-border px-3 pt-3">
              <button
                type="button"
                onClick={() => setTab("mp4")}
                className={`flex items-center gap-2 rounded-t-md px-4 py-2.5 text-sm font-medium transition-colors ${
                  tab === "mp4"
                    ? "border-b-2 border-foreground text-foreground"
                    : "border-b-2 border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Video className="h-4 w-4" />
                Video (MP4)
              </button>
              <button
                type="button"
                onClick={() => setTab("mp3")}
                className={`flex items-center gap-2 rounded-t-md px-4 py-2.5 text-sm font-medium transition-colors ${
                  tab === "mp3"
                    ? "border-b-2 border-foreground text-foreground"
                    : "border-b-2 border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Music className="h-4 w-4" />
                Audio (MP3)
              </button>
            </div>

            <ul className="divide-y divide-border">
              {formats.map((f) => (
                <li
                  key={f.quality}
                  className="flex items-center justify-between px-5 py-3.5"
                >
                  <div className="flex items-center gap-3">
                    <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      {tab}
                    </span>
                    <span className="text-sm font-medium">{f.quality}</span>
                  </div>
                  <a
                    href={getDownloadUrl(url.trim(), tab, f.quality)}
                    className="inline-flex h-8 items-center gap-2 rounded-lg px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                  >
                    <Download className="h-4 w-4" />
                    Download
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section id="how" className="mt-24 grid gap-8 sm:grid-cols-3">
          {[
            {
              n: "01",
              t: "Copy a link",
              d: "Grab the URL from any YouTube video.",
            },
            {
              n: "02",
              t: "Pick a format",
              d: "MP4 video or MP3 audio, your choice of quality.",
            },
            {
              n: "03",
              t: "Download",
              d: "Save the file straight to your device.",
            },
          ].map((s) => (
            <div key={s.n}>
              <div className="text-xs font-medium tracking-widest text-muted-foreground">
                {s.n}
              </div>
              <div className="mt-2 text-sm font-medium">{s.t}</div>
              <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-6 text-xs text-muted-foreground">
          <span>© {new Date().getFullYear()} Loop</span>
          <span>Made for personal use only.</span>
        </div>
      </footer>
    </div>
  );
}
