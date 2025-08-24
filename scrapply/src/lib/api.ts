// API helper functions for interacting with the backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ScrapingRequest {
  url: string;
  description: string;
  user_id?: string;
}

export interface JobResponse {
  id: string;
  url: string;
  description: string;
  status: 'pending' | 'analyzing' | 'generating' | 'testing' | 'ready' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  api_endpoint_path?: string;
            sample_data?: Record<string, unknown> | Record<string, unknown>[];
          error_info?: Record<string, unknown>;
          analysis?: Record<string, unknown>;
}

export interface JobList {
  jobs: JobResponse[];
  total: number;
  page: number;
  size: number;
}

// Create a new scraping request
export async function createScrapingRequest(request: ScrapingRequest): Promise<JobResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/requests`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to create scraping request: ${response.statusText}`);
  }

  return response.json();
}

// Get job status
export async function getJobStatus(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/jobs/${jobId}`);

  if (!response.ok) {
    throw new Error(`Failed to get job status: ${response.statusText}`);
  }

  return response.json();
}

// List jobs
export async function listJobs(limit: number = 10, offset: number = 0, status?: string): Promise<JobList> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  if (status) {
    params.append('status', status);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/jobs?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to list jobs: ${response.statusText}`);
  }

  return response.json();
}

// Delete job
export async function deleteJob(jobId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/jobs/${jobId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete job: ${response.statusText}`);
  }
}

// Retry job
export async function retryJob(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/jobs/${jobId}/retry`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to retry job: ${response.statusText}`);
  }

  return response.json();
}

// Test generated API
export async function testApiEndpoint(jobId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE_URL}/generated/${jobId}/test`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to test API endpoint: ${response.statusText}`);
  }

  return response.json();
}

// Execute generated API
export async function executeApiEndpoint(jobId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE_URL}/generated/${jobId}`);

  if (!response.ok) {
    throw new Error(`Failed to execute API endpoint: ${response.statusText}`);
  }

  return response.json();
}

// Get API info
export async function getApiInfo(jobId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE_URL}/generated/${jobId}/info`);

  if (!response.ok) {
    throw new Error(`Failed to get API info: ${response.statusText}`);
  }

  return response.json();
}
