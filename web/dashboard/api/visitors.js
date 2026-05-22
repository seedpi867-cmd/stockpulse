import { put, head } from '@vercel/blob';

const BLOB_PATH = 'visitors/data.json';

async function loadData() {
  try {
    const blob = await head(BLOB_PATH);
    if (blob) {
      // Cache-bust by adding timestamp query param
      const url = new URL(blob.url);
      url.searchParams.set('t', Date.now());
      const res = await fetch(url.toString(), { cache: 'no-store' });
      return await res.json();
    }
  } catch {}
  return { total: 0, seen: {} };
}

async function saveData(data) {
  await put(BLOB_PATH, JSON.stringify(data), {
    access: 'public',
    addRandomSuffix: false,
    allowOverwrite: true,
  });
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const now = Math.floor(Date.now() / 1000);

  if (req.method === 'POST') {
    try {
      const { id } = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
      if (!id) return res.status(400).json({ error: 'missing id' });

      const data = await loadData();

      // New unique visitor
      if (!data.seen[id]) {
        data.total += 1;
      }

      // Update heartbeat timestamp
      data.seen[id] = now;

      // Prune visitors older than 5 minutes
      const cutoff = now - 300;
      const pruned = {};
      for (const [k, v] of Object.entries(data.seen)) {
        if (v > cutoff) pruned[k] = v;
      }
      data.seen = pruned;

      await saveData(data);

      const liveCutoff = now - 120;
      const live = Object.values(data.seen).filter(v => v > liveCutoff).length;

      return res.status(200).json({ live, total: data.total });
    } catch (e) {
      return res.status(500).json({ error: e.message });
    }
  }

  // GET
  try {
    const data = await loadData();
    const liveCutoff = now - 120;
    const live = Object.values(data.seen).filter(v => v > liveCutoff).length;
    return res.status(200).json({ live, total: data.total });
  } catch (e) {
    return res.status(200).json({ live: 0, total: 0 });
  }
}
