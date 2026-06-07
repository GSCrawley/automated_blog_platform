import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, ExternalLink, AlertCircle, CheckCircle2, ArrowDownToLine, ArrowUpFromLine, Lightbulb } from 'lucide-react'
import { blogApi, reviewApi, proposalsApi } from '@/services/api'

/**
 * PublishedArticles (PR #6) — list of articles already on Ghost with
 * drift indicators.
 *
 * Drift fan-out: the doc spec says "rate-limited, parallel fan-out capped
 * at 4". This implementation keeps it sequential to avoid hammering the
 * Ghost API and to keep the code straightforward; with realistic queue
 * sizes (single-digit articles in early days) the latency is fine. PR #7+
 * can revisit if the queue grows large.
 *
 * Pull-from-Ghost / Push-to-Ghost are surfaced inline; the manual diff
 * view lives in ArticleReview.jsx (the row's "Open" link).
 */
const PublishedArticles = () => {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [driftMap, setDriftMap] = useState({})  // article_id -> {drift_detected, diverging_fields}
  const [busy, setBusy] = useState(null)        // article_id currently being pulled/pushed
  const [improvMap, setImprovMap] = useState({}) // article_id -> pending improvement count

  const refresh = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await blogApi.getArticles({ status: 'published', limit: 200 })
      if (data.success) {
        setItems(data.articles || [])
      } else {
        setError(data.error || 'Failed to load published articles.')
      }
    } catch (err) {
      setError(err.message || 'Network error.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  // After the initial load, walk the queue and fetch drift status for each.
  useEffect(() => {
    if (loading || items.length === 0) return
    let cancelled = false
    ;(async () => {
      for (const a of items) {
        if (cancelled) return
        if (a.ghost_post_id) {
          try {
            const data = await reviewApi.ghostSnapshot(a.id)
            if (cancelled) return
            if (data.success) {
              setDriftMap((prev) => ({
                ...prev,
                [a.id]: {
                  drift_detected: data.drift_detected,
                  diverging_fields: data.diverging_fields,
                },
              }))
            }
          } catch {
            // Ignore — leave the row without an indicator.
          }
        }
        // Fetch pending improvement count for each article
        try {
          const impData = await proposalsApi.getImprovements(a.id, { status: 'pending' })
          if (cancelled) return
          if (impData.success) {
            setImprovMap((prev) => ({
              ...prev,
              [a.id]: (impData.proposals || []).length,
            }))
          }
        } catch {
          // Non-critical; omit badge if request fails.
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [loading, items])

  const handlePull = async (article) => {
    if (
      !confirm(
        `Overwrite local copy of "${article.title}" with Ghost's version?\n\n` +
          `A snapshot of the local state will be saved first.`,
      )
    ) {
      return
    }
    setBusy(article.id)
    try {
      const data = await reviewApi.pullFromGhost(article.id)
      if (data.success) {
        setDriftMap((prev) => ({
          ...prev,
          [article.id]: { drift_detected: false, diverging_fields: [] },
        }))
        await refresh()
      } else {
        alert(`Pull failed: ${data.error || 'unknown error'}`)
      }
    } catch (err) {
      alert(`Pull failed: ${err.message || 'network error'}`)
    } finally {
      setBusy(null)
    }
  }

  const handlePush = async (article) => {
    if (
      !confirm(
        `Overwrite Ghost's "${article.title}" with the local version?\n\n` +
          `A snapshot of Ghost's current state will be saved first.`,
      )
    ) {
      return
    }
    setBusy(article.id)
    try {
      const data = await reviewApi.pushToGhost(article.id)
      if (data.success) {
        setDriftMap((prev) => ({
          ...prev,
          [article.id]: { drift_detected: false, diverging_fields: [] },
        }))
        await refresh()
      } else {
        alert(`Push failed: ${data.error || 'unknown error'}`)
      }
    } catch (err) {
      alert(`Push failed: ${err.message || 'network error'}`)
    } finally {
      setBusy(null)
    }
  }

  const driftIndicator = (article) => {
    if (!article.ghost_post_id) return null
    const entry = driftMap[article.id]
    if (entry === undefined) {
      return (
        <Badge variant="secondary" className="gap-1">
          <RefreshCw className="h-3 w-3 animate-spin" />
          checking
        </Badge>
      )
    }
    if (entry.drift_detected) {
      return (
        <Badge variant="destructive" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          drift
        </Badge>
      )
    }
    return (
      <Badge variant="default" className="gap-1">
        <CheckCircle2 className="h-3 w-3" />
        in sync
      </Badge>
    )
  }

  const formatDate = (s) =>
    s
      ? new Date(s).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : '—'

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Published Articles</h1>
          <p className="text-muted-foreground">
            Articles live on Ghost. Drift indicator shows whether local and Ghost agree.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="h-6 w-6 animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-sm text-muted-foreground">
            No articles have been published yet.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((a) => {
            const entry = driftMap[a.id]
            return (
              <Card key={a.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-lg">
                        <Link to={`/review/${a.id}`} className="hover:underline">
                          {a.title}
                        </Link>
                      </CardTitle>
                      <CardDescription>
                        {a.niche_name && <>{a.niche_name} · </>}
                        published {formatDate(a.updated_at)}
                        {a.published_url && (
                          <>
                            {' · '}
                            <a
                              href={a.published_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-600 hover:underline inline-flex items-center gap-1"
                            >
                              Open ↗
                            </a>
                          </>
                        )}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {driftIndicator(a)}
                      {improvMap[a.id] > 0 && (
                        <Link to={`/review/${a.id}`} title="Open improvement proposals">
                          <Badge variant="outline" className="gap-1 border-yellow-400 text-yellow-700">
                            <Lightbulb className="h-3 w-3" />
                            {improvMap[a.id]} improvement{improvMap[a.id] !== 1 ? 's' : ''}
                          </Badge>
                        </Link>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 flex items-center justify-between flex-wrap gap-2">
                  <div className="text-xs text-muted-foreground font-mono">
                    {a.ghost_post_id ? `ghost: ${a.ghost_post_id}` : 'no ghost_post_id'}
                    {entry?.diverging_fields?.length > 0 && (
                      <span className="ml-3 text-amber-700">
                        diverging: {entry.diverging_fields.join(', ')}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePull(a)}
                      disabled={busy === a.id || !a.ghost_post_id}
                    >
                      <ArrowDownToLine className="h-4 w-4 mr-1" />
                      Pull
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePush(a)}
                      disabled={busy === a.id || !a.ghost_post_id}
                      title={
                        a.editorial_verdict !== 'PUBLISH'
                          ? 'Verdict must be PUBLISH to push.'
                          : ''
                      }
                    >
                      <ArrowUpFromLine className="h-4 w-4 mr-1" />
                      Push
                    </Button>
                    <Button asChild size="sm">
                      <Link to={`/review/${a.id}`}>Review</Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default PublishedArticles
