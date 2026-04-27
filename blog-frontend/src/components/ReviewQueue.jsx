import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, ExternalLink, Eye } from 'lucide-react'
import { reviewApi } from '@/services/api'

/**
 * ReviewQueue (PR #6) — the dedicated review screen.
 *
 * The Dashboard already shows the queue in a compact card; this component
 * is the richer view with verdict / blueprint / cost / per-axis pass-fail
 * surfaced inline so a reviewer can triage without opening every article.
 */
const ReviewQueue = () => {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [verdictFilter, setVerdictFilter] = useState('') // '' | PUBLISH | REJECT
  const [sort, setSort] = useState('updated_at')

  const refresh = async () => {
    setLoading(true)
    setError(null)
    try {
      const filters = { sort, limit: 100 }
      if (verdictFilter) filters.editorial_verdict = verdictFilter
      const data = await reviewApi.getQueue(filters)
      if (data.success) {
        setItems(data.articles || [])
        setTotal(data.total || 0)
      } else {
        setError('Failed to load queue.')
      }
    } catch (err) {
      setError(err.message || 'Network error.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [verdictFilter, sort])

  const verdictBadge = (verdict) => {
    if (!verdict || verdict === 'PENDING') return <Badge variant="secondary">PENDING</Badge>
    if (verdict === 'PUBLISH') return <Badge variant="default">PUBLISH</Badge>
    return <Badge variant="destructive">REJECT</Badge>
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
          <h1 className="text-3xl font-bold tracking-tight">Review Queue</h1>
          <p className="text-muted-foreground">
            Articles awaiting human review. Click an item to open the review screen.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6 flex items-center gap-4 flex-wrap">
          <label className="text-sm">
            Verdict:{' '}
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="ml-1 px-2 py-1 border rounded"
            >
              <option value="">All</option>
              <option value="PUBLISH">PUBLISH</option>
              <option value="REJECT">REJECT</option>
            </select>
          </label>
          <label className="text-sm">
            Sort:{' '}
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="ml-1 px-2 py-1 border rounded"
            >
              <option value="updated_at">Last updated</option>
              <option value="cost_usd">Cost (high → low)</option>
            </select>
          </label>
          <span className="text-sm text-muted-foreground">
            {total} article{total === 1 ? '' : 's'} in queue
          </span>
        </CardContent>
      </Card>

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
            Queue is empty.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((a) => {
            const summary = a.editorial_report_summary || {}
            const axisScores = summary.axis_scores || {}
            return (
              <Card key={a.id} className="hover:shadow-md transition-shadow">
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
                        {a.word_count} words · ${Number(a.cost_usd || 0).toFixed(2)} ·
                        updated {formatDate(a.updated_at)}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {verdictBadge(a.editorial_verdict)}
                      <Button asChild size="sm">
                        <Link to={`/review/${a.id}`}>
                          <Eye className="h-4 w-4 mr-1" />
                          Review
                        </Link>
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid gap-2 md:grid-cols-4 text-xs">
                    {Object.entries(axisScores).map(([axis, score]) => (
                      <div
                        key={axis}
                        className="flex items-center justify-between p-2 border rounded"
                      >
                        <span className="capitalize text-muted-foreground">
                          {axis.replace('_', ' ')}
                        </span>
                        <span className="font-mono font-medium">
                          {typeof score === 'number' ? score.toFixed(1) : score}
                        </span>
                      </div>
                    ))}
                  </div>
                  {a.blueprint_id && (
                    <div className="mt-2 text-xs text-muted-foreground font-mono">
                      blueprint: {a.blueprint_id}
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default ReviewQueue
