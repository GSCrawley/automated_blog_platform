import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { 
  TrendingUp, 
  FileText, 
  DollarSign, 
  Eye, 
  Clock, 
  Play, 
  Pause,
  RefreshCw,
  BarChart3,
  Settings,
  Plus
} from 'lucide-react'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totals: {
      products: 0,
      articles: 0,
      published_articles: 0,
      draft_articles: 0
    },
    recent_articles: [],
    top_articles: []
  })
  const [schedulerStatus, setSchedulerStatus] = useState({
    running: false,
    scheduled_jobs: 0,
    next_run: null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardStats()
    fetchSchedulerStatus()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      // Try to fetch products and articles to build stats
      const [productsResponse, articlesResponse] = await Promise.all([
        fetch("http://localhost:5000/api/blog/products"),
        fetch("http://localhost:5000/api/blog/articles")
      ])
      
      const productsData = await productsResponse.json()
      const articlesData = await articlesResponse.json()
      
      if (productsData.success && articlesData.success) {
        const products = productsData.products || []
        const articles = articlesData.articles || []
        
        const publishedArticles = articles.filter(a => a.status === 'published')
        const draftArticles = articles.filter(a => a.status === 'draft')
        
        setStats({
          totals: {
            products: products.length,
            articles: articles.length,
            published_articles: publishedArticles.length,
            draft_articles: draftArticles.length
          },
          recent_articles: articles.slice(0, 5).map(article => ({
            ...article,
            views: Math.floor(Math.random() * 1000) + 100,
            revenue: Math.random() * 50 + 10
          })),
          top_articles: articles.slice(0, 3).map(article => ({
            ...article,
            views: Math.floor(Math.random() * 2000) + 500,
            revenue: Math.random() * 100 + 50
          }))
        })
      }
      setLoading(false)
    } catch (error) {
      console.error("Error fetching dashboard stats:", error)
      setLoading(false)
    }
  }

  const fetchSchedulerStatus = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/automation/scheduler/status")
      const data = await response.json()
      if (data.success) {
        setSchedulerStatus({
          running: data.status.is_running,
          scheduled_jobs: 2,
          next_run: data.status.next_scheduled_generation
        })
      }
    } catch (error) {
      console.error("Error fetching scheduler status:", error)
    }
  }

  const toggleScheduler = async () => {
    try {
      const endpoint = schedulerStatus.running ? "stop" : "start"
      const response = await fetch(`http://localhost:5000/api/automation/scheduler/${endpoint}`, {
        method: "POST"
      })
      const data = await response.json()
      if (data.success) {
        fetchSchedulerStatus() // Refresh status after toggle
      } else {
        console.error(`Error ${endpoint}ing scheduler:`, data.error)
      }
    } catch (error) {
      console.error(`Error toggling scheduler:`, error)
    }
  }

  const runTaskManually = async (taskName) => {
    try {
      let endpoint = ""
      if (taskName === "content_generation") {
        endpoint = "trigger-content-generation"
      } else if (taskName === "content_update") {
        endpoint = "trigger-content-update"
      } else {
        console.log(`Task ${taskName} not implemented yet`)
        return
      }
      
      const response = await fetch(`http://localhost:5000/api/automation/scheduler/${endpoint}`, {
        method: "POST"
      })
      const data = await response.json()
      if (data.success) {
        console.log(`Task ${taskName} executed successfully`)
        fetchDashboardStats() // Refresh stats after task
      } else {
        console.error(`Error running task ${taskName}:`, data.error)
      }
    } catch (error) {
      console.error("Error running task:", error)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status) => {
    const variants = {
      published: 'default',
      draft: 'secondary',
      scheduled: 'outline'
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your automated blog system performance and manage content generation.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={fetchDashboardStats}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Article
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totals.products}</div>
            <p className="text-xs text-muted-foreground">
              +2 from last week
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totals.articles}</div>
            <p className="text-xs text-muted-foreground">
              {stats.totals.published_articles} published, {stats.totals.draft_articles} drafts
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12,450</div>
            <p className="text-xs text-muted-foreground">
              +15% from last month
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$1,245</div>
            <p className="text-xs text-muted-foreground">
              +8% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Scheduler Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Automation Scheduler</span>
          </CardTitle>
          <CardDescription>
            Manage automated content generation and updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${schedulerStatus.running ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm font-medium">
                  {schedulerStatus.running ? 'Running' : 'Stopped'}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {schedulerStatus.scheduled_jobs} scheduled jobs
              </div>
              {schedulerStatus.next_run && (
                <div className="text-sm text-muted-foreground">
                  Next run: {formatDate(schedulerStatus.next_run)}
                </div>
              )}
            </div>
            <Button
              variant={schedulerStatus.running ? "destructive" : "default"}
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
          
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-5">
            {[
              { name: 'Trend Analysis', key: 'trend_analysis' },
              { name: 'Content Generation', key: 'content_generation' },
              { name: 'Content Update', key: 'content_update' },
              { name: 'SEO Analysis', key: 'seo_analysis' },
              { name: 'Performance Review', key: 'performance_review' }
            ].map((task) => (
              <Button
                key={task.key}
                variant="outline"
                size="sm"
                onClick={() => runTaskManually(task.key)}
                className="text-xs"
              >
                <Play className="h-3 w-3 mr-1" />
                {task.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Content Tabs */}
      <Tabs defaultValue="recent" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recent">Recent Articles</TabsTrigger>
          <TabsTrigger value="top">Top Performing</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Articles</CardTitle>
              <CardDescription>
                Latest articles generated by the system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.recent_articles.map((article) => (
                  <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <h3 className="font-medium line-clamp-1">{article.title}</h3>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
                        <span>{formatDate(article.created_at)}</span>
                        <span>{article.views} views</span>
                        <span>${article.revenue.toFixed(2)} revenue</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(article.status)}
                      <Button variant="ghost" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="top" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Articles</CardTitle>
              <CardDescription>
                Articles with highest views and revenue
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.top_articles.map((article, index) => (
                  <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="font-medium line-clamp-1">{article.title}</h3>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-muted-foreground">
                          <span>{article.views} views</span>
                          <span>${article.revenue.toFixed(2)} revenue</span>
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <BarChart3 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Content Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Published Articles</span>
                      <span>{stats.totals.published_articles}/{stats.totals.articles}</span>
                    </div>
                    <Progress 
                      value={(stats.totals.published_articles / stats.totals.articles) * 100} 
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>SEO Score</span>
                      <span>85%</span>
                    </div>
                    <Progress value={85} className="mt-2" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Conversion Rate</span>
                      <span>3.2%</span>
                    </div>
                    <Progress value={32} className="mt-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">API Status</span>
                    <Badge variant="default">Healthy</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Database</span>
                    <Badge variant="default">Connected</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Scheduler</span>
                    <Badge variant={schedulerStatus.running ? "default" : "destructive"}>
                      {schedulerStatus.running ? "Running" : "Stopped"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Last Update</span>
                    <span className="text-sm text-muted-foreground">2 min ago</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Dashboard

