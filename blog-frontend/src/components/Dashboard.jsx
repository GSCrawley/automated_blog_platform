import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import {
  TrendingUp,
  FileText,
  DollarSign,
  Clock,
  Play,
  Pause,
  RefreshCw,
  Settings,
  Plus,
  Inbox,
} from 'lucide-react'
import { blogApi, automationApi } from '@/services/api'

/**
 * Dashboard (PR #4).
 *
 * Surfaces the data this stack actually has — counts by current_stage and
 * editorial_verdict, the human-review queue, and the monthly cost-vs-cap bar
 * from PR #3's budget panel. The mock "views" / "revenue" tiles from earlier
 * iterations were removed; PR #7 will replace them with real GSC + affiliate
 * data.
 */
const Dashboard = () => {
  const [stats, setStats] = useState(null)
  const [reviewQueue, setReviewQueue] = useState([])
  const [recentArticles, setRecentArticles] = useState([])
  const [schedulerStatus, setSchedulerStatus] = useState({
    running: false,
    scheduled_jobs: 0,
    next_run: null,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    refresh()
    fetchSchedulerStatus()
  }, [])

  const refresh = async () => {
    setLoading(true)
    try {
      const [statsRes, queueRes, recentRes] = await Promise.all([
        blogApi.getDashboardStats(),
        blogApi.getArticles({ current_stage: 'awaiting_human_review', limit: 50 }),
        blogApi.getArticles({ limit: 5 }),
      ])
      if (statsRes.success) setStats(statsRes.stats)
      if (queueRes.success) setReviewQueue(queueRes.articles || [])
      if (recentRes.success) setRecentArticles(recentRes.articles || [])
    } catch (err) {
      console.error('Error refreshing dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchSchedulerStatus = async () => {
    try {
      const data = await automationApi.getSchedulerStatus()
      if (data.success) {
        setSchedulerStatus({
          running: data.status.is_running,
          scheduled_jobs: 2,
          next_run: data.status.next_scheduled_generation,
        })
      }
    } catch (err) {
      console.error('Error fetching scheduler status:', err)
    }
  }

  const toggleScheduler = async () => {
    try {
      const data = schedulerStatus.running
        ? await automationApi.stopScheduler()
        : await automationApi.startScheduler()
      if (data.success) fetchSchedulerStatus()
    } catch (err) {
      console.error('Error toggling scheduler:', err)
    }
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

  const verdictBadge = (verdict) => {
    if (!verdict || verdict === 'PENDING') return <Badge variant="secondary">PENDING</Badge>
    if (verdict === 'PUBLISH') return <Badge variant="default">PUBLISH</Badge>
    return <Badge variant="destructive">REJECT</Badge>
  }

  const stageBadge = (stage) => {
    if (!stage) return null
    const variant = stage === 'awaiting_human_review' ? 'default' : 'outline'
    return <Badge variant={variant}>{stage}</Badge>
  }

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  const cost = stats.cost || { spent_usd: 0, cap_usd: 100, pct_used: 0, month: '' }
  const byStage = stats.by_stage || {}
  const byVerdict = stats.by_verdict || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Pipeline state, human-review queue, and monthly cost vs cap.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={refresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button asChild size="sm">
            <Link to="/articles">
              <Plus className="h-4 w-4 mr-2" />
              New Article
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats cards — real numbers only */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Products</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.products}</div>
            <p className="text-xs text-muted-foreground">across {stats.niches} active niches</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Articles</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.articles}</div>
            <p className="text-xs text-muted-foreground">
              PUBLISH {byVerdict.PUBLISH || 0} · REJECT {byVerdict.REJECT || 0} · PENDING{' '}
              {byVerdict.PENDING || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Awaiting Review</CardTitle>
            <Inbox className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.awaiting_review}</div>
            <p className="text-xs text-muted-foreground">human queue (PR #6 surfaces this)</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost — {cost.month}</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${cost.spent_usd.toFixed(2)}{' '}
              <span className="text-sm font-normal text-muted-foreground">
                / ${cost.cap_usd.toFixed(0)}
              </span>
            </div>
            <Progress value={Math.min(cost.pct_used, 100)} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">{cost.pct_used.toFixed(1)}% used</p>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline by stage */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline state</CardTitle>
          <CardDescription>Active (non-archived) articles by current_stage.</CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(byStage).length === 0 ? (
            <p className="text-sm text-muted-foreground">No articles in flight.</p>
          ) : (
            <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4">
              {Object.entries(byStage)
                .sort(([, a], [, b]) => b - a)
                .map(([stage, count]) => (
                  <div
                    key={stage}
                    className="flex items-center justify-between p-3 border rounded-md"
                  >
                    <span className="text-sm font-medium truncate">{stage}</span>
                    <span className="text-lg font-bold">{count}</span>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scheduler */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Automation Scheduler</span>
          </CardTitle>
          <CardDescription>Manage automated content generation and updates.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div
                  className={`h-2 w-2 rounded-full ${
                    schedulerStatus.running ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span className="text-sm font-medium">
                  {schedulerStatus.running ? 'Running' : 'Stopped'}
                </span>
              </div>
              {schedulerStatus.next_run && (
                <div className="text-sm text-muted-foreground">
                  Next run: {formatDate(schedulerStatus.next_run)}
                </div>
              )}
            </div>
            <Button
              variant={schedulerStatus.running ? 'destructive' : 'default'}
              size="sm"
              onClick={toggleScheduler}
            >
              {schedulerStatus.running ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabs: review queue + recent articles */}
      <Tabs defaultValue="queue" className="space-y-4">
        <TabsList>
          <TabsTrigger value="queue">
            Review Queue
            {stats.awaiting_review > 0 && (
              <Badge variant="secondary" className="ml-2">
                {stats.awaiting_review}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="recent">Recent Articles</TabsTrigger>
        </TabsList>

        <TabsContent value="queue" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Articles awaiting human review</CardTitle>
              <CardDescription>
                Editorial completed; the human is in the loop (PR #6 will publish from here).
              </CardDescription>
            </CardHeader>
            <CardContent>
              {reviewQueue.length === 0 ? (
                <p className="text-sm text-muted-foreground">Queue is empty.</p>
              ) : (
                <div className="space-y-2">
                  {reviewQueue.map((article) => (
                    <div
                      key={article.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <Link
                          to={`/articles/${article.id}`}
                          className="font-medium line-clamp-1 hover:underline"
                        >
                          {article.title}
                        </Link>
                        <div className="flex items-center space-x-3 mt-2 text-xs text-muted-foreground">
                          <span>updated {formatDate(article.updated_at)}</span>
                          {article.cost_usd != null && (
                            <span>${Number(article.cost_usd).toFixed(2)} spent</span>
                          )}
                          {article.blueprint_id && <span>bp: {article.blueprint_id}</span>}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {verdictBadge(article.editorial_verdict)}
                        {stageBadge(article.current_stage)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Articles</CardTitle>
              <CardDescription>Latest activity across all niches.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {recentArticles.map((article) => (
                  <div
                    key={article.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <Link
                        to={`/articles/${article.id}`}
                        className="font-medium line-clamp-1 hover:underline"
                      >
                        {article.title}
                      </Link>
                      <div className="flex items-center space-x-3 mt-2 text-xs text-muted-foreground">
                        <span>created {formatDate(article.created_at)}</span>
                        {article.published_url && (
                          <a
                            href={article.published_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            live ↗
                          </a>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {verdictBadge(article.editorial_verdict)}
                      {stageBadge(article.current_stage)}
                      <Button asChild variant="ghost" size="sm">
                        <Link to={`/articles/${article.id}`}>
                          <Settings className="h-4 w-4" />
                        </Link>
                      </Button>
                    </div>
                  </div>
                ))}
                {recentArticles.length === 0 && (
                  <p className="text-sm text-muted-foreground">No articles yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Dashboard
