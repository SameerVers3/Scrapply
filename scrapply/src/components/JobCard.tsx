'use client';

import { useState } from 'react';
import { JobResponse } from '@/lib/api';
import { deleteJob, retryJob, testApiEndpoint, executeApiEndpoint } from '@/lib/api';
import { Clock, CheckCircle, XCircle, Loader2, Play, TestTube, Trash2, RotateCcw } from 'lucide-react';
import ProgressBar from './ProgressBar';

interface JobCardProps {
  job: JobResponse;
  onJobUpdated: () => void;
}

export default function JobCard({ job, onJobUpdated }: JobCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [showTestResult, setShowTestResult] = useState(false);

  const getStatusIcon = () => {
    switch (job.status) {
      case 'pending':
      case 'analyzing':
      case 'generating':
      case 'testing':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'ready':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (job.status) {
      case 'pending':
      case 'analyzing':
      case 'generating':
      case 'testing':
        return 'text-yellow-700 bg-yellow-100';
      case 'ready':
        return 'text-green-700 bg-green-100';
      case 'failed':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job?')) return;
    
    setIsLoading(true);
    try {
      await deleteJob(job.id);
      onJobUpdated();
    } catch (error) {
      console.error('Failed to delete job:', error);
      alert('Failed to delete job');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = async () => {
    setIsLoading(true);
    try {
      await retryJob(job.id);
      onJobUpdated();
    } catch (error) {
      console.error('Failed to retry job:', error);
      alert('Failed to retry job');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTest = async () => {
    setIsLoading(true);
    try {
      const result = await testApiEndpoint(job.id);
      setTestResult(result);
      setShowTestResult(true);
    } catch (error) {
      console.error('Failed to test API:', error);
      alert('Failed to test API');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecute = async () => {
    setIsLoading(true);
    try {
      const result = await executeApiEndpoint(job.id);
      setTestResult(result);
      setShowTestResult(true);
    } catch (error) {
      console.error('Failed to execute API:', error);
      alert('Failed to execute API');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <h3 className="text-lg font-medium text-gray-900 truncate max-w-xs">
                {job.url}
              </h3>
              <p className="text-sm text-gray-500">{job.description}</p>
            </div>
          </div>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor()}`}>
            {job.status}
          </span>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{job.progress}%</span>
          </div>
          <ProgressBar progress={job.progress} />
        </div>

        {job.message && (
          <div className="mb-4 text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
            {job.message}
          </div>
        )}

        {job.api_endpoint_path && (
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700 mb-1">API Endpoint:</p>
            <code className="text-xs bg-gray-100 p-2 rounded block break-all">
              {job.api_endpoint_path}
            </code>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Created: {new Date(job.created_at).toLocaleDateString()}
          </div>
          
          <div className="flex items-center space-x-2">
            {job.status === 'ready' && (
              <>
                <button
                  onClick={handleTest}
                  disabled={isLoading}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                >
                  <TestTube className="h-4 w-4" />
                  <span>Test</span>
                </button>
                <button
                  onClick={handleExecute}
                  disabled={isLoading}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 disabled:opacity-50"
                >
                  <Play className="h-4 w-4" />
                  <span>Execute</span>
                </button>
              </>
            )}
            
            {job.status === 'failed' && (
              <button
                onClick={handleRetry}
                disabled={isLoading}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 disabled:opacity-50"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Retry</span>
              </button>
            )}
            
            <button
              onClick={handleDelete}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              <span>Delete</span>
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="mt-4 flex items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          </div>
        )}
      </div>

      {/* Test Result Modal */}
      {showTestResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">API Result</h3>
              <button
                onClick={() => setShowTestResult(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
              {JSON.stringify(testResult, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </>
  );
}
