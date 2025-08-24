'use client';

import { useState } from 'react';
import { Settings, User, Shield, Bell, Palette, Database, Key } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'appearance', name: 'Appearance', icon: Palette },
    { id: 'api', name: 'API Settings', icon: Key },
    { id: 'data', name: 'Data & Storage', icon: Database },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
              <Settings className="w-4 h-4 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          </div>
          <p className="text-muted-foreground">Manage your account and preferences</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">
                  {tabs.find(tab => tab.id === activeTab)?.name}
                </h2>
                <p className="card-description">
                  {activeTab === 'profile' && 'Manage your account information and preferences'}
                  {activeTab === 'security' && 'Update your password and security settings'}
                  {activeTab === 'notifications' && 'Configure how you receive notifications'}
                  {activeTab === 'appearance' && 'Customize the look and feel of the application'}
                  {activeTab === 'api' && 'Manage your API keys and endpoints'}
                  {activeTab === 'data' && 'Control your data and storage settings'}
                </p>
              </div>
              
              <div className="card-content">
                {activeTab === 'profile' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Display Name
                      </label>
                      <input
                        type="text"
                        placeholder="Enter your display name"
                        className="input"
                        defaultValue="John Doe"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        placeholder="Enter your email"
                        className="input"
                        defaultValue="john@example.com"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Bio
                      </label>
                      <textarea
                        placeholder="Tell us about yourself"
                        rows={3}
                        className="textarea"
                        defaultValue="Web developer and data enthusiast"
                      />
                    </div>
                    
                    <button className="btn btn-primary">
                      Save Changes
                    </button>
                  </div>
                )}

                {activeTab === 'security' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Current Password
                      </label>
                      <input
                        type="password"
                        placeholder="Enter current password"
                        className="input"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        placeholder="Enter new password"
                        className="input"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        placeholder="Confirm new password"
                        className="input"
                      />
                    </div>
                    
                    <button className="btn btn-primary">
                      Update Password
                    </button>
                  </div>
                )}

                {activeTab === 'notifications' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-foreground">Email Notifications</h3>
                        <p className="text-sm text-muted-foreground">Receive email updates about your APIs</p>
                      </div>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-foreground">API Status Updates</h3>
                        <p className="text-sm text-muted-foreground">Get notified when your APIs are ready</p>
                      </div>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-foreground">Error Alerts</h3>
                        <p className="text-sm text-muted-foreground">Receive alerts when APIs fail</p>
                      </div>
                      <input type="checkbox" className="rounded" />
                    </div>
                    
                    <button className="btn btn-primary">
                      Save Preferences
                    </button>
                  </div>
                )}

                {activeTab === 'appearance' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Theme
                      </label>
                      <select className="input">
                        <option>System</option>
                        <option>Light</option>
                        <option>Dark</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Font Size
                      </label>
                      <select className="input">
                        <option>Small</option>
                        <option>Medium</option>
                        <option>Large</option>
                      </select>
                    </div>
                    
                    <button className="btn btn-primary">
                      Apply Changes
                    </button>
                  </div>
                )}

                {activeTab === 'api' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        API Base URL
                      </label>
                      <input
                        type="url"
                        placeholder="https://api.scrapply.com"
                        className="input"
                        defaultValue="https://api.scrapply.com"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Rate Limit
                      </label>
                      <select className="input">
                        <option>100 requests/hour</option>
                        <option>1000 requests/hour</option>
                        <option>Unlimited</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Timeout (seconds)
                      </label>
                      <input
                        type="number"
                        placeholder="30"
                        className="input"
                        defaultValue="30"
                      />
                    </div>
                    
                    <button className="btn btn-primary">
                      Update API Settings
                    </button>
                  </div>
                )}

                {activeTab === 'data' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                      <div>
                        <h3 className="font-medium text-foreground">Storage Used</h3>
                        <p className="text-sm text-muted-foreground">2.4 GB of 10 GB</p>
                      </div>
                      <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                        <Database className="w-6 h-6 text-primary" />
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-foreground">Auto-delete Old Data</h3>
                        <p className="text-sm text-muted-foreground">Automatically delete data older than 30 days</p>
                      </div>
                      <input type="checkbox" className="rounded" />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-foreground">Data Export</h3>
                        <p className="text-sm text-muted-foreground">Export your data as JSON or CSV</p>
                      </div>
                      <button className="btn btn-outline btn-sm">
                        Export
                      </button>
                    </div>
                    
                    <div className="border-t border-border pt-4">
                      <button className="btn btn-destructive">
                        Delete All Data
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
