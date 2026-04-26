import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, RefreshCw, ExternalLink } from 'lucide-react'
import { blogApi } from '@/services/api'

/**
 * ArticleDetail (PR #4) — read-only view of an article's stage outputs.
 *
 * Five tabs, each pretty-prints the corresponding `*_json` column from
 * Article (the four PR #3 stage columns plus the PR #2 EditorialVerdict).
 * Inline editing arrives in PR #6 — this screen is just a window into what
 * the pipeline produced.
 */
const ArticleDetail = () => {
  const { id } = useParams()
  const [article, setArticle] = useState(null)
  const [stageOutputs, setStageOutputs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = async () => {
    setLoading(true)
    setError(null)
    try {
      const [a, so] = await Promise.all([
        blogApi.getArticle(id),
        blogApi.getArticleStageOutputs(id),
      ])
      if (a.success) setArticle(a.article)
      if (so.success) setStageOutputs(so)
    } catch (err) {
      setError(err.message || 'Failed to load article.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (error || !article) {
    return (
      <div className="p-6">
        <Button asChild variant="ghost" size="sm">
          <Link to="/articles">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Articles
          </Link>
        </Button>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4">
          {error || 'Article not found.'}
        </div>
      </div>
    )
  }

  const verdict = (article.editorial_verdict || 'PENDING').toUpperCase()
  const verdictVariant =
    verdict === 'PUBLISH' ? 'default' : verdict === 'REJECT' ? 'destructive' : 'secondary'

  const so = stageOutputs?.stage_outputs || {}

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Button asChild variant="ghost" size="sm">
            <Link to="/articles">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Articles
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">{article.title}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant={verdictVariant}>{verdict}</Badge>
            {article.current_stage && (
              <Badge variant="outline">{article.current_stage}</Badge>
            )}
            {article.niche_name && <span>· {article.niche_name}</span>}
            {article.product_name && <span>· {article.product_name}</span>}
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Top-level metadata strip */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              ${Number(stageOutputs?.cost_usd ?? 0).toFixed(2)}
              {stageOutputs?.cost_budget_usd != null && (
                <span className="text-sm font-normal text-muted-foreground">
                  {' '}
                  / ${Number(stageOutputs.cost_budget_usd).toFixed(2)}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Word count</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{article.word_count || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Blueprint</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs font-mono break-all">
              {stageOutputs?.blueprint_id || article.blueprint_id || '—'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Published URL</CardTitle>
          </CardHeader>
          <CardContent>
            {article.published_url ? (
              <a
                href={article.published_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:underline text-sm flex items-center gap-1"
              >
                Open <ExternalLink className="h-3 w-3" />
              </a>
            ) : (
              <span className="text-sm text-muted-foreground">—</span>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Stage tabs */}
      <Tabs defaultValue="research" className="space-y-4">
        <TabsList>
          <TabsTrigger value="research">Research</TabsTrigger>
          <TabsTrigger value="strategy">Strategy</TabsTrigger>
          <TabsTrigger value="draft">Draft</TabsTrigger>
          <TabsTrigger value="monetization">Monetization</TabsTrigger>
          <TabsTrigger value="verdict">Editorial Report</TabsTrigger>
        </TabsList>

        <TabsContent value="research">
          <StagePanel
            title="Research report"
            description="Stage 0 output. Real-time intelligence gathering (Tavily / Serper / Firecrawl)."
            data={so.research_report}
          />
        </TabsContent>
        <TabsContent value="strategy">
          <StagePanel
            title="Content strategy"
            description="Stage 1 output. Topic plan derived from research."
            data={so.strategy}
          />
        </TabsContent>
        <TabsContent value="draft">
          <StagePanel
            title="Draft sections"
            description="Stage 2 output. Article draft."
            data={so.draft_sections}
          />
        </TabsContent>
        <TabsContent value="monetization">
          <StagePanel
            title="Monetization map"
            description="Affiliate placements + CTAs."
            data={so.monetization_map}
          />
        </TabsContent>
        <TabsContent value="verdict">
          <EditorialReportPanel data={so.editorial_verdict} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

const StagePanel = ({ title, description, data }) => {
  const formatted = useMemo(() => {
    if (data == null) return null
    if (typeof data === 'string') return data
    try {
      return JSON.stringify(data, null, 2)
    } catch {
      return String(data)
    }
  }, [data])

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {formatted == null ? (
          <p className="text-sm text-muted-foreground">No data persisted for this stage yet.</p>
        ) : (
          <pre className="bg-gray-50 border rounded p-4 text-xs overflow-x-auto max-h-[600px]">
            {formatted}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}

const EditorialReportPanel = ({ data }) => {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Editorial Report</CardTitle>
          <CardDescription>No verdict has been written yet.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  // Normalize: data might be the EditorialVerdict JSON or a wrapped object.
  const verdict = data.verdict || 'PENDING'
  const axisReports = Array.isArray(data.axis_reports) ? data.axis_reports : []
  const blocking = Array.isArray(data.blocking_axes) ? data.blocking_axes : []
  const variant = verdict === 'PUBLISH' ? 'default' : verdict === 'REJECT' ? 'destructive' : 'secondary'

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Editorial Report</CardTitle>
            <CardDescription>
              Conformance / Quality / Monetization / Compliance — scored against the active Blueprint.
            </CardDescription>
          </div>
          <Badge variant={variant}>{verdict}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {blocking.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-sm">
            <strong>Blocking axes:</strong> {blocking.join(', ')}
          </div>
        )}

        {axisReports.length === 0 ? (
          <p className="text-sm text-muted-foreground">No axis reports in the saved verdict.</p>
        ) : (
          axisReports.map((report) => (
            <AxisCard key={report.axis} report={report} />
          ))
        )}
      </CardContent>
    </Card>
  )
}

const AxisCard = ({ report }) => {
  const score = typeof report.score === 'number' ? report.score.toFixed(1) : String(report.score)
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold capitalize">{report.axis.replace('_', ' ')}</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{score} / 10</span>
          <Badge variant={report.passed ? 'default' : 'destructive'}>
            {report.passed ? 'pass' : 'fail'}
          </Badge>
        </div>
      </div>

      {Array.isArray(report.checklist) && report.checklist.length > 0 && (
        <ul className="text-sm space-y-1">
          {report.checklist.map((item, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className={item.passed ? 'text-green-600' : 'text-red-600'}>
                {item.passed ? '✓' : '✗'}
              </span>
              <span className="flex-1">
                <span className="font-mono text-xs">{item.item}</span>
                {item.expected !== undefined && item.actual !== undefined && (
                  <span className="text-muted-foreground ml-2">
                    expected {JSON.stringify(item.expected)} · actual {JSON.stringify(item.actual)}
                  </span>
                )}
                {item.note && (
                  <span className="text-muted-foreground italic ml-2">— {item.note}</span>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default ArticleDetail
