import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  Eye, 
  Users, 
  MousePointer,
  Calendar,
  Target
} from 'lucide-react';

const Analytics = () => {
  const [analytics, setAnalytics] = useState({
    overview: {
      totalViews: 0,
      totalRevenue: 0,
      conversionRate: 0,
      avgTimeOnPage: 0
    },
    topArticles: [],
    revenueByNiche: [],
    trafficSources: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      // Simulate analytics data since we don't have real analytics yet
      const mockAnalytics = {
        overview: {
          totalViews: 45230,
          totalRevenue: 3420.50,
          conversionRate: 3.2,
          avgTimeOnPage: 245
        },
        topArticles: [
          { title: "Best Protein Powders 2024", views: 8450, revenue: 420.30, conversionRate: 4.2 },
          { title: "MacBook Pro M3 Review", views: 6230, revenue: 380.50, conversionRate: 3.8 },
          { title: "Top Gaming Headsets", views: 5120, revenue: 290.20, conversionRate: 3.1 },
          { title: "Fitness Tracker Comparison", views: 4890, revenue: 245.80, conversionRate: 2.9 },
          { title: "Best Coding Bootcamps", views: 4320, revenue: 520.40, conversionRate: 5.1 }
        ],
        revenueByNiche: [
          { niche: "Health & Fitness", revenue: 1250.30, percentage: 36.5 },
          { niche: "Technology", revenue: 980.20, percentage: 28.7 },
          { niche: "Education", revenue: 720.50, percentage: 21.1 },
          { niche: "Gaming", revenue: 469.50, percentage: 13.7 }
        ],
        trafficSources: [
          { source: "Organic Search", visitors: 18920, percentage: 65.2 },
          { source: "Social Media", visitors: 5430, percentage: 18.7 },
          { source: "Direct", visitors: 3210, percentage: 11.1 },
          { source: "Referral", visitors: 1450, percentage: 5.0 }
        ]
      };
      
      setAnalytics(mockAnalytics);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <BarChart3 className="h-8 w-8 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Track your blog performance and revenue metrics.
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.overview.totalViews)}</div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.overview.totalRevenue)}</div>
            <p className="text-xs text-muted-foreground">
              +8% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.overview.conversionRate}%</div>
            <p className="text-xs text-muted-foreground">
              +0.3% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Time on Page</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.floor(analytics.overview.avgTimeOnPage / 60)}m {analytics.overview.avgTimeOnPage % 60}s</div>
            <p className="text-xs text-muted-foreground">
              +15s from last month
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="articles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="articles">Top Articles</TabsTrigger>
          <TabsTrigger value="niches">Revenue by Niche</TabsTrigger>
          <TabsTrigger value="traffic">Traffic Sources</TabsTrigger>
        </TabsList>

        <TabsContent value="articles" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Articles</CardTitle>
              <CardDescription>
                Articles with highest views and revenue
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.topArticles.map((article, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="font-medium">{article.title}</h3>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-muted-foreground">
                          <span>{formatNumber(article.views)} views</span>
                          <span>{formatCurrency(article.revenue)} revenue</span>
                          <Badge variant="outline">{article.conversionRate}% conversion</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="niches" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Revenue by Niche</CardTitle>
              <CardDescription>
                Performance breakdown by product category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.revenueByNiche.map((niche, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{niche.niche}</span>
                      <span className="text-sm text-muted-foreground">
                        {formatCurrency(niche.revenue)} ({niche.percentage}%)
                      </span>
                    </div>
                    <Progress value={niche.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traffic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Traffic Sources</CardTitle>
              <CardDescription>
                Where your visitors are coming from
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.trafficSources.map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted">
                        {source.source === 'Organic Search' && <TrendingUp className="h-5 w-5" />}
                        {source.source === 'Social Media' && <Users className="h-5 w-5" />}
                        {source.source === 'Direct' && <MousePointer className="h-5 w-5" />}
                        {source.source === 'Referral' && <BarChart3 className="h-5 w-5" />}
                      </div>
                      <div>
                        <div className="font-medium">{source.source}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatNumber(source.visitors)} visitors
                        </div>
                      </div>
                    </div>
                    <Badge variant="outline">{source.percentage}%</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;

