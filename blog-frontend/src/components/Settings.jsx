import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Save, Key, Globe, DollarSign, User, Shield } from 'lucide-react';

const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    // User Account
    user_name: '',
    user_email: '',
    
  // (Removed WordPress credentials in headless architecture pivot)
    
    // Blog Configuration
    blog_target_url: '',
    blog_title: '',
    blog_description: '',
    blog_niche: '',
    
    // Affiliate Program Credentials
    amazon_associates_tag: '',
    amazon_access_key: '',
    amazon_secret_key: '',
    clickbank_nickname: '',
    clickbank_api_key: '',
    commission_junction_website_id: '',
    commission_junction_api_key: '',
    shareasale_merchant_id: '',
    shareasale_token: '',
    
    // OpenAI API
    openai_api_key: '',
    
    // Other API Keys
    serp_api_key: '',
    ahrefs_api_key: '',
    semrush_api_key: ''
  });

  const handleInputChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // TODO: Implement API call to save settings
      // const response = await userApi.updateSettings(settings);
      
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Configure your account and affiliate program settings.
          </p>
        </div>
        <Button onClick={handleSave} disabled={loading}>
          <Save className="h-4 w-4 mr-2" />
          {loading ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {saved && (
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            Settings saved successfully!
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="account" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="account">
            <User className="h-4 w-4 mr-2" />
            Account
          </TabsTrigger>
          {/* WordPress tab removed */}
          <TabsTrigger value="blog">
            <Globe className="h-4 w-4 mr-2" />
            Blog Config
          </TabsTrigger>
          <TabsTrigger value="affiliate">
            <DollarSign className="h-4 w-4 mr-2" />
            Affiliate Programs
          </TabsTrigger>
          <TabsTrigger value="apis">
            <Key className="h-4 w-4 mr-2" />
            API Keys
          </TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Account</CardTitle>
              <CardDescription>
                Your basic account information.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="user_name">Full Name</Label>
                <Input
                  id="user_name"
                  placeholder="Your full name"
                  value={settings.user_name}
                  onChange={(e) => handleInputChange('user_name', e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="user_email">Email Address</Label>
                <Input
                  id="user_email"
                  type="email"
                  placeholder="your.email@example.com"
                  value={settings.user_email}
                  onChange={(e) => handleInputChange('user_email', e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

  {/* WordPress credentials content removed */}

        <TabsContent value="blog" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Blog Configuration</CardTitle>
              <CardDescription>
                Configure your automated blog settings and target niche.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="blog_target_url">Blog Target URL</Label>
                <Input
                  id="blog_target_url"
                  placeholder="https://yourblog.com"
                  value={settings.blog_target_url}
                  onChange={(e) => handleInputChange('blog_target_url', e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="blog_title">Blog Title</Label>
                <Input
                  id="blog_title"
                  placeholder="Your Blog Title"
                  value={settings.blog_title}
                  onChange={(e) => handleInputChange('blog_title', e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="blog_description">Blog Description</Label>
                <Textarea
                  id="blog_description"
                  placeholder="A brief description of your blog's focus and purpose"
                  value={settings.blog_description}
                  onChange={(e) => handleInputChange('blog_description', e.target.value)}
                  rows={3}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="blog_niche">Primary Niche</Label>
                <Input
                  id="blog_niche"
                  placeholder="e.g., Men's Health, Tech Reviews, Fitness"
                  value={settings.blog_niche}
                  onChange={(e) => handleInputChange('blog_niche', e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  Declaring a niche will trigger automated product discovery and affiliate program setup.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="affiliate" className="space-y-4">
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Amazon Associates</CardTitle>
                <CardDescription>
                  Configure your Amazon Associates affiliate program.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="amazon_associates_tag">Associates Tag</Label>
                  <Input
                    id="amazon_associates_tag"
                    placeholder="yourtag-20"
                    value={settings.amazon_associates_tag}
                    onChange={(e) => handleInputChange('amazon_associates_tag', e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="amazon_access_key">Access Key</Label>
                  <Input
                    id="amazon_access_key"
                    placeholder="Your Amazon API access key"
                    value={settings.amazon_access_key}
                    onChange={(e) => handleInputChange('amazon_access_key', e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="amazon_secret_key">Secret Key</Label>
                  <Input
                    id="amazon_secret_key"
                    type="password"
                    placeholder="Your Amazon API secret key"
                    value={settings.amazon_secret_key}
                    onChange={(e) => handleInputChange('amazon_secret_key', e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Other Affiliate Programs</CardTitle>
                <CardDescription>
                  Configure additional affiliate program credentials.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="clickbank_nickname">ClickBank Nickname</Label>
                    <Input
                      id="clickbank_nickname"
                      placeholder="Your ClickBank nickname"
                      value={settings.clickbank_nickname}
                      onChange={(e) => handleInputChange('clickbank_nickname', e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="clickbank_api_key">ClickBank API Key</Label>
                    <Input
                      id="clickbank_api_key"
                      placeholder="Your ClickBank API key"
                      value={settings.clickbank_api_key}
                      onChange={(e) => handleInputChange('clickbank_api_key', e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="commission_junction_website_id">CJ Website ID</Label>
                    <Input
                      id="commission_junction_website_id"
                      placeholder="Commission Junction Website ID"
                      value={settings.commission_junction_website_id}
                      onChange={(e) => handleInputChange('commission_junction_website_id', e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="commission_junction_api_key">CJ API Key</Label>
                    <Input
                      id="commission_junction_api_key"
                      placeholder="Commission Junction API key"
                      value={settings.commission_junction_api_key}
                      onChange={(e) => handleInputChange('commission_junction_api_key', e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="shareasale_merchant_id">ShareASale Merchant ID</Label>
                    <Input
                      id="shareasale_merchant_id"
                      placeholder="ShareASale Merchant ID"
                      value={settings.shareasale_merchant_id}
                      onChange={(e) => handleInputChange('shareasale_merchant_id', e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="shareasale_token">ShareASale Token</Label>
                    <Input
                      id="shareasale_token"
                      placeholder="ShareASale API token"
                      value={settings.shareasale_token}
                      onChange={(e) => handleInputChange('shareasale_token', e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="apis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>
                Configure API keys for content generation and SEO analysis.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="openai_api_key">OpenAI API Key</Label>
                <Input
                  id="openai_api_key"
                  type="password"
                  placeholder="sk-..."
                  value={settings.openai_api_key}
                  onChange={(e) => handleInputChange('openai_api_key', e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  Required for automated content generation.
                </p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="serp_api_key">SERP API Key</Label>
                <Input
                  id="serp_api_key"
                  placeholder="Your SERP API key"
                  value={settings.serp_api_key}
                  onChange={(e) => handleInputChange('serp_api_key', e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="ahrefs_api_key">Ahrefs API Key</Label>
                <Input
                  id="ahrefs_api_key"
                  placeholder="Your Ahrefs API key"
                  value={settings.ahrefs_api_key}
                  onChange={(e) => handleInputChange('ahrefs_api_key', e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="semrush_api_key">SEMrush API Key</Label>
                <Input
                  id="semrush_api_key"
                  placeholder="Your SEMrush API key"
                  value={settings.semrush_api_key}
                  onChange={(e) => handleInputChange('semrush_api_key', e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;
