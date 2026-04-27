import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, RefreshCw, Save, Send, FileX, ExternalLink, AlertCircle } from 'lucide-react'
import { reviewApi } from '@/services/api'

/**
 * ArticleReview (PR #6) — the human-in-the-loop review + publish surface.
 *
 * Layout:
 *   Left  — tabbed editor (Content / SEO / CTAs).
 *   Right — Editorial Report, Blueprint Conformance, Ghost Preview, costs.
 *   Footer — Save / Publish to Ghost / Unpublish / Discard.
 *
 * Behaviors:
 *   - Save = PATCH /api/review/<id>
 *   - Publish = POST /api/review/<id>/publish (verdict-gated; confirm modal first)
 *   - Unpublish = POST /api/review/<id>/unpublish
 *   - Autosave runs every 30s while there are dirty edits.
 *
 * The doc's "Tiptap" rich-text editor is intentionally not wired here —
 * PR #6 ships with HTML / sections / SEO inputs as plain controls so the
 * data path is observable. A richer editor can land as a follow-up.
 */
const ArticleReview = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [bundle, setBundle] = useState(null)   // full /api/review/<id> response
  const [draft, setDraft] = useState(null)     // editable copy
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [confirmPublish, setConfirmPublish] = useState(false)
  const [toast, setToast] = useState(null)     // {kind, msg}
  const lastSavedJSON = useRef('')

  const refresh = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await reviewApi.getArticle(id)
      if (data.success) {
        setBundle(data)
        const editable = {
          title: data.article.title || '',
          content: data.article.content || '',
          meta_description: data.article.meta_description || '',
          keywords: data.article.keywords || [],
        }
        setDraft(editable)
        lastSavedJSON.current = JSON.stringify(editable)
      } else {
        setError(data.error || 'Failed to load article.')
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
  }, [id])

  // Track dirty state.
  const isDirty = useMemo(() => {
    if (!draft) return false
    return JSON.stringify(draft) !== lastSavedJSON.current
  }, [draft])

  const showToast = (kind, msg) => {
    setToast({ kind, msg })
    setTimeout(() => setToast(null), 4000)
  }

  const save = async ({ silent = false } = {}) => {
    if (!draft || !isDirty) return
    setSaving(true)
    try {
      const body = {
        title: draft.title,
        content: draft.content,
        meta_description: draft.meta_description,
        keywords: draft.keywords,
      }
      const data = await reviewApi.patch(id, body)
      if (data.success) {
        setBundle(data)
        lastSavedJSON.current = JSON.stringify(draft)
        if (!silent) showToast('success', 'Saved.')
      } else {
        showToast('error', data.error || 'Save failed.')
      }
    } catch (err) {
      showToast('error', err.message || 'Save failed.')
    } finally {
      setSaving(false)
    }
  }

  // Autosave every 30 seconds while dirty + tab focused.
  useEffect(() => {
    if (!isDirty) return
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') save({ silent: true })
    }, 30000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDirty])

  const publish = async () => {
    setConfirmPublish(false)
    setPublishing(true)
    try {
      const data = await reviewApi.publish(id)
      if (data.success) {
        showToast('success', `Published to Ghost.`)
        await refresh()
      } else {
        showToast('error', data.error || 'Publish failed.')
      }
    } catch (err) {
      showToast('error', err.message || 'Publish failed.')
    } finally {
      setPublishing(false)
    }
  }

  const unpublish = async () => {
    if (!confirm('Set Ghost post to draft? The article remains in our database.')) return
    setSaving(true)
    try {
      const data = await reviewApi.unpublish(id)
      if (data.success) {
        showToast('success', 'Ghost post set to draft.')
        await refresh()
      } else {
        showToast('error', data.error || 'Unpublish failed.')
      }
    } catch (err) {
      showToast('error', err.message || 'Unpublish failed.')
    } finally {
      setSaving(false)
    }
  }

  const discard = () => {
    if (isDirty && !confirm('Discard unsaved changes?')) return
    refresh()
  }

  if (loading || !bundle || !draft) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 space-y-4">
        <Button asChild variant="ghost" size="sm">
          <Link to="/review">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Queue
          </Link>
        </Button>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    )
  }

  const article = bundle.article
  const verdict = (article.editorial_verdict || 'PENDING').toUpperCase()
  const verdictVariant =
    verdict === 'PUBLISH' ? 'default' : verdict === 'REJECT' ? 'destructive' : 'secondary'
  const ghostPreview = bundle.ghost_preview || {}
  const editorialReport = bundle.editorial_report
  const ghostSync = bundle.ghost_sync || {}
  const isPublished = article.status === 'published'
  const canPublish = verdict === 'PUBLISH' && !isDirty && !publishing

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2 flex-1 min-w-0">
          <Button asChild variant="ghost" size="sm">
            <Link to="/review">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Queue
            </Link>
          </Button>
          <h1 className="text-2xl font-bold tracking-tight truncate">{article.title}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge variant={verdictVariant}>{verdict}</Badge>
            {article.current_stage && <Badge variant="outline">{article.current_stage}</Badge>}
            {isDirty && <Badge variant="secondary">unsaved edits</Badge>}
            {ghostSync.drift_detected && (
              <Badge variant="destructive">drift</Badge>
            )}
            {article.niche_name && <span>· {article.niche_name}</span>}
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={`px-4 py-3 rounded text-sm ${
            toast.kind === 'success'
              ? 'bg-green-100 border border-green-400 text-green-800'
              : 'bg-red-100 border border-red-400 text-red-700'
          }`}
        >
          {toast.msg}
          {ghostSync.published_url && toast.kind === 'success' && (
            <>
              {' '}
              <a
                href={article.published_url || ghostSync.published_url}
                target="_blank"
                rel="noreferrer"
                className="underline"
              >
                Open ↗
              </a>
            </>
          )}
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-[55fr_45fr]">
        {/* LEFT: Editor */}
        <div className="space-y-4">
          <Tabs defaultValue="content">
            <TabsList>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="seo">SEO</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <TabsContent value="content" className="space-y-3">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Title</CardTitle>
                </CardHeader>
                <CardContent>
                  <input
                    type="text"
                    value={draft.title}
                    onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                    className="w-full px-3 py-2 border rounded"
                  />
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Content (HTML)</CardTitle>
                  <CardDescription>
                    Edit the raw HTML. Preview tab renders the final Ghost payload.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <textarea
                    value={draft.content}
                    onChange={(e) => setDraft({ ...draft, content: e.target.value })}
                    rows={24}
                    className="w-full px-3 py-2 border rounded font-mono text-xs"
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="seo" className="space-y-3">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Meta description</CardTitle>
                  <CardDescription>
                    {draft.meta_description.length} / 160 — Ghost truncates to 156.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <textarea
                    value={draft.meta_description}
                    onChange={(e) =>
                      setDraft({ ...draft, meta_description: e.target.value })
                    }
                    rows={3}
                    maxLength={160}
                    className="w-full px-3 py-2 border rounded text-sm"
                  />
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Keywords (tags on Ghost)</CardTitle>
                  <CardDescription>Comma-separated, max 10.</CardDescription>
                </CardHeader>
                <CardContent>
                  <input
                    type="text"
                    value={(draft.keywords || []).join(', ')}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        keywords: e.target.value
                          .split(',')
                          .map((s) => s.trim())
                          .filter(Boolean)
                          .slice(0, 10),
                      })
                    }
                    className="w-full px-3 py-2 border rounded text-sm"
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="preview">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Ghost preview</CardTitle>
                  <CardDescription>
                    Exact HTML payload Ghost will receive.
                    {isDirty && ' Save to refresh this view.'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <iframe
                    title="Ghost preview"
                    srcDoc={`<style>body{font-family:system-ui;padding:1rem;max-width:65ch;margin:0 auto;}h2{margin-top:1.5em;}</style>${ghostPreview.html || ''}`}
                    className="w-full border rounded bg-white"
                    style={{ height: '600px' }}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* RIGHT: Editorial report + sync */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                Editorial Report
                <Badge variant={verdictVariant}>{verdict}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EditorialReportPanel report={editorialReport} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Cost &amp; metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cost so far</span>
                <span>
                  ${Number(article.cost_usd || 0).toFixed(2)}
                  {article.cost_budget_usd && (
                    <span className="text-muted-foreground">
                      {' '}/ ${Number(article.cost_budget_usd).toFixed(2)}
                    </span>
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Word count</span>
                <span>{article.word_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Blueprint</span>
                <span className="font-mono text-xs truncate ml-2">
                  {article.blueprint_id || '—'}
                </span>
              </div>
              {article.published_url && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Published URL</span>
                  <a
                    href={article.published_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1 text-xs"
                  >
                    Open <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}
              {ghostSync.drift_detected && (
                <div className="flex items-start gap-2 mt-2 p-2 rounded bg-amber-50 border border-amber-200 text-amber-800 text-xs">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>
                    Local has unpushed changes. Pull from Ghost to discard, or
                    push to overwrite Ghost.
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer actions */}
      <div className="flex items-center justify-end gap-2 sticky bottom-0 bg-background border-t pt-4 -mx-6 px-6">
        <Button variant="outline" onClick={discard} disabled={!isDirty}>
          Discard
        </Button>
        {isPublished && (
          <Button variant="outline" onClick={unpublish} disabled={saving}>
            <FileX className="h-4 w-4 mr-2" />
            Unpublish
          </Button>
        )}
        <Button onClick={() => save()} disabled={!isDirty || saving}>
          <Save className="h-4 w-4 mr-2" />
          {saving ? 'Saving…' : 'Save Draft'}
        </Button>
        <Button
          onClick={() => setConfirmPublish(true)}
          disabled={!canPublish}
          title={
            verdict !== 'PUBLISH'
              ? 'Verdict must be PUBLISH to publish.'
              : isDirty
              ? 'Save your edits first.'
              : 'Publish to Ghost.'
          }
        >
          <Send className="h-4 w-4 mr-2" />
          {isPublished ? 'Push to Ghost' : 'Publish to Ghost'}
        </Button>
      </div>

      {/* Confirm publish modal */}
      {confirmPublish && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-auto">
            <CardHeader>
              <CardTitle>Confirm publish</CardTitle>
              <CardDescription>
                The exact payload below will be sent to Ghost. This is the only
                action that creates / updates the live post.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1 text-sm">
                <div>
                  <strong>Title:</strong> {ghostPreview.title}
                </div>
                <div>
                  <strong>Slug:</strong> {ghostPreview.slug || article.slug || '(auto)'}
                </div>
                <div>
                  <strong>Tags:</strong>{' '}
                  {(ghostPreview.tags || []).map((t) => t.name).join(', ') || '—'}
                </div>
                <div>
                  <strong>Meta description:</strong> {ghostPreview.meta_description || '—'}
                </div>
              </div>
              <div className="border rounded">
                <pre className="text-xs p-3 bg-gray-50 max-h-60 overflow-auto">
                  {(ghostPreview.html || '').slice(0, 500)}
                  {(ghostPreview.html || '').length > 500 ? '\n...' : ''}
                </pre>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setConfirmPublish(false)}>
                  Cancel
                </Button>
                <Button onClick={publish} disabled={publishing}>
                  <Send className="h-4 w-4 mr-2" />
                  {publishing ? 'Publishing…' : 'Confirm publish'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

const EditorialReportPanel = ({ report }) => {
  if (!report) {
    return <p className="text-sm text-muted-foreground">No verdict yet.</p>
  }
  const blocking = Array.isArray(report.blocking_axes) ? report.blocking_axes : []
  const reports = Array.isArray(report.axis_reports) ? report.axis_reports : []
  return (
    <div className="space-y-3">
      {blocking.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded p-2 text-xs">
          <strong>Blocking axes:</strong> {blocking.join(', ')}
        </div>
      )}
      {reports.map((r) => (
        <div key={r.axis} className="border rounded p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium capitalize">{r.axis.replace('_', ' ')}</span>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground">{Number(r.score).toFixed(1)} / 10</span>
              <Badge variant={r.passed ? 'default' : 'destructive'}>
                {r.passed ? 'pass' : 'fail'}
              </Badge>
            </div>
          </div>
          {Array.isArray(r.checklist) && r.checklist.length > 0 && (
            <ul className="text-xs space-y-1">
              {r.checklist.slice(0, 6).map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className={item.passed ? 'text-green-600' : 'text-red-600'}>
                    {item.passed ? '✓' : '✗'}
                  </span>
                  <span className="font-mono">{item.item}</span>
                </li>
              ))}
              {r.checklist.length > 6 && (
                <li className="text-muted-foreground italic">
                  …and {r.checklist.length - 6} more
                </li>
              )}
            </ul>
          )}
        </div>
      ))}
    </div>
  )
}

export default ArticleReview
