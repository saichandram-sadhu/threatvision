/** Placeholder route — full MISP Explorer UI ships in M14. Linked from dashboard MISP health widget. */
export default function MispExplorerPlaceholderPage() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold text-tv-fg">MISP Explorer</h1>
      <p className="max-w-xl text-tv-muted">
        Detailed feeds, servers, taxonomies, and sync status will appear here in milestone M14 after you connect
        MISP under integrations.
      </p>
    </div>
  );
}
