const API_BASE = import.meta.env.VITE_API_URL ?? "/api";

export type FormatOption = {
  quality: string;
  format_id: string;
};

export type VideoInfo = {
  title: string;
  thumbnail: string;
  duration: number;
  duration_formatted: string;
  channel: string;
  view_count: number;
  upload_date: string | null;
  formats: {
    mp3: FormatOption[];
    mp4: FormatOption[];
  };
};

export type ApiError = {
  error: true;
  code: number;
  message: string;
};

export async function fetchVideoInfo(url: string): Promise<VideoInfo> {
  const params = new URLSearchParams({ url });
  const response = await fetch(`${API_BASE}/info?${params}`);

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiError | null;
    throw new Error(body?.message ?? "Failed to fetch video info");
  }

  return response.json() as Promise<VideoInfo>;
}

export function getDownloadUrl(
  url: string,
  format: "mp3" | "mp4",
  quality: string,
): string {
  const params = new URLSearchParams({ url, format, quality });
  return `${API_BASE}/download?${params}`;
}
