import { useRef, useState } from "react";
import { useAuthenticatedUrl } from "../hooks/useAuthenticatedUrl";

interface AudioPlayerProps {
  src?: string;
  filename?: string;
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function AudioPlayerComponent({ src: srcProp, filename }: AudioPlayerProps) {
  const { url: src, loading, error } = useAuthenticatedUrl(srcProp);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);

  if (!srcProp) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-6 text-center text-sm text-gray-400 dark:text-gray-500">
        No audio source provided
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-6 text-center text-sm text-gray-400 dark:text-gray-500 animate-pulse">
        Loading audio…
      </div>
    );
  }

  const toggle = () => {
    const el = audioRef.current;
    if (!el) return;
    playing ? el.pause() : el.play();
    setPlaying(!playing);
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const el = audioRef.current;
    if (!el) return;
    el.currentTime = Number(e.target.value);
    setCurrent(Number(e.target.value));
  };

  const changeVolume = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Number(e.target.value);
    setVolume(v);
    if (audioRef.current) audioRef.current.volume = v;
  };

  const progress = duration > 0 ? (current / duration) * 100 : 0;
  const trackBg = `linear-gradient(to right, #4f46e5 ${progress}%, #e5e7eb ${progress}%)`;

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={() => setCurrent(audioRef.current?.currentTime ?? 0)}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration ?? 0)}
        onEnded={() => setPlaying(false)}
      />

      {/* Header — keeps the indigo gradient in both modes for identity */}
      <div className="px-4 py-3 bg-gradient-to-r from-indigo-700 to-indigo-500 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z" />
          </svg>
        </div>
        <div className="min-w-0">
          <p className="text-white font-medium text-sm truncate">{filename ?? "Audio File"}</p>
          <p className="text-indigo-200 text-xs">
            {error ? "Failed to load" : duration > 0 ? formatTime(duration) : "Loading…"}
          </p>
        </div>
        {!error && (
          <a href={src} download={filename} className="ml-auto text-white/70 hover:text-white text-xs flex-shrink-0" title="Download">
            ↓ Save
          </a>
        )}
      </div>

      {error ? (
        <div className="px-4 py-3 text-sm text-red-500 dark:text-red-400 text-center">
          Could not load audio.{" "}
          <a href={src} className="underline" target="_blank" rel="noreferrer">Open directly</a>
        </div>
      ) : (
        <div className="px-4 py-4 space-y-3">
          {/* Progress bar */}
          <div className="space-y-1">
            <input
              type="range"
              min={0}
              max={duration || 1}
              step={0.1}
              value={current}
              onChange={seek}
              className="w-full h-1.5 rounded-full accent-indigo-500 cursor-pointer"
              style={{ background: trackBg }}
            />
            <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500">
              <span>{formatTime(current)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => { if (audioRef.current) audioRef.current.currentTime = Math.max(0, current - 10); }}
              className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              title="Back 10s"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 0 0 0 1.6l5.334 4A1 1 0 0 0 19 16V8a1 1 0 0 0-1.6-.8l-5.334 4ZM4.066 11.2a1 1 0 0 0 0 1.6l5.334 4A1 1 0 0 0 11 16V8a1 1 0 0 0-1.6-.8l-5.334 4Z" />
              </svg>
            </button>

            <button
              onClick={toggle}
              className="w-10 h-10 rounded-full bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center text-white transition-colors shadow-sm"
            >
              {playing ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4h4v16H6zm8 0h4v16h-4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>

            <button
              onClick={() => { if (audioRef.current) audioRef.current.currentTime = Math.min(duration, current + 10); }}
              className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              title="Forward 10s"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.933 12.8a1 1 0 0 0 0-1.6L6.6 7.2A1 1 0 0 0 5 8v8a1 1 0 0 0 1.6.8l5.333-4ZM19.933 12.8a1 1 0 0 0 0-1.6l-5.333-4A1 1 0 0 0 13 8v8a1 1 0 0 0 1.6.8l5.333-4Z" />
              </svg>
            </button>
          </div>

          {/* Volume */}
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 7.97v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
            </svg>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={changeVolume}
              className="w-24 h-1.5 rounded-full accent-indigo-500 cursor-pointer"
            />
          </div>
        </div>
      )}
    </div>
  );
}
