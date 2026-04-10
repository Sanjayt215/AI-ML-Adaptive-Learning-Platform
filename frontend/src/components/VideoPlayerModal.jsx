import React, { useEffect, useState } from 'react';

const YOUTUBE_ID_REGEX = /(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/))([A-Za-z0-9_-]{11})/;

function parseYouTubeId(url) {
  if (!url) return null;
  const match = url.match(YOUTUBE_ID_REGEX);
  return match ? match[1] : null;
}

export default function VideoPlayerModal({ open, video, onClose, onWatchUpdate }) {
  const [watchedPct, setWatchedPct] = useState(0);
  const [watchedSeconds, setWatchedSeconds] = useState(0);
  const videoId = parseYouTubeId(video?.url || '');

  useEffect(() => {
    if (!open) {
      setWatchedPct(0);
      setWatchedSeconds(0);
    }
  }, [open]);

  if (!open || !video) {
    return null;
  }

  const handleMarkWatch = (pct) => {
    const seconds = Math.max(watchedSeconds, Math.round((pct / 100) * 240));
    setWatchedPct(pct);
    setWatchedSeconds(seconds);
    onWatchUpdate({ watched_seconds: seconds, watched_pct: pct, event: pct >= 80 ? 'complete' : 'progress' });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80">
      <div className="w-full max-w-4xl rounded-3xl bg-slate-950 border border-white/10 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div>
            <div className="text-sm font-semibold text-white">Embedded video player</div>
            <div className="text-xs text-slate-400">{video?.title}</div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm">Close</button>
        </div>
        <div className="bg-black/95 p-4">
          {videoId ? (
            <div className="aspect-video w-full rounded-2xl overflow-hidden border border-white/10">
              <iframe
                title={video.title}
                src={`https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`}
                allow="autoplay; encrypted-media"
                allowFullScreen
                className="w-full h-full"
              />
            </div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-slate-900 p-6 text-center text-slate-300">
              <div className="mb-3 text-sm">This video cannot be embedded inside the player.</div>
              <a href={video.url} target="_blank" rel="noreferrer" className="btn-cyber">Open on external site</a>
            </div>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-5 border-t border-white/10">
          <button onClick={() => handleMarkWatch(40)} className="btn-cyber">Mark 40% watched</button>
          <button onClick={() => handleMarkWatch(80)} className="btn-cyber-solid">Mark 80% watched</button>
          <button onClick={() => handleMarkWatch(100)} className="btn-cyber">Mark Completed</button>
        </div>
        <div className="px-5 pb-5 text-xs text-slate-500">
          Use the embedded player to watch the topic video. Tracking sends watched progress to the backend even when content is embedded.
        </div>
      </div>
    </div>
  );
}
