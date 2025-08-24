import { useCallback, useEffect, useRef, useState } from 'react';
import { JobResponse, getJobStatus } from './api';

interface UseJobStreamOptions {
  jobId: string | null;
  onUpdate?: (job: JobResponse) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

export function useJobStream({ jobId, onUpdate, onError, onComplete }: UseJobStreamOptions) {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usePolling, setUsePolling] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(false);
  const latestJobRef = useRef<JobResponse | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Polling fallback function
  const startPolling = useCallback(() => {
    if (!jobId || !mountedRef.current) return;
    
    const poll = async () => {
      try {
        const jobData = await getJobStatus(jobId!);
        if (mountedRef.current) {
          setJob(jobData);
    latestJobRef.current = jobData;
          onUpdate?.(jobData);
          
          // Stop polling if job is complete
          if (jobData.status === 'ready' || jobData.status === 'failed') {
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            onComplete?.();
          }
        }
      } catch (err) {
        if (mountedRef.current) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to fetch job status';
          setError(errorMessage);
          onError?.(errorMessage);
        }
      }
    };

    // Initial poll
    poll();
    
    // Set up polling interval
    pollingIntervalRef.current = setInterval(poll, 3000);
  }, [jobId, onUpdate, onError, onComplete]);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;

    if (!jobId) {
      setIsConnected(false);
      setJob(null);
      setError(null);
      setUsePolling(false);
      return;
    }

    // Close existing connections
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // Try SSE first
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const eventSource = new EventSource(`${API_BASE_URL}/api/v1/scraping/jobs/stream/${jobId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      if (mountedRef.current) {
        setIsConnected(true);
        setError(null);
        setUsePolling(false);
      }
    };

    eventSource.onmessage = (e) => {
      if (!mountedRef.current) return;
      
      try {
        const data = JSON.parse(e.data);
        
        if (data.error) {
          setError(data.error);
          onError?.(data.error);
          eventSource.close();
          // Fallback to polling
          setUsePolling(true);
          startPolling();
          return;
        }

        // Convert the stream data to JobResponse format
        const jobUpdate: JobResponse = {
          id: data.id,
          url: latestJobRef.current?.url || '', // prefer latest known
          description: latestJobRef.current?.description || '',
          status: data.status,
          progress: data.progress,
          message: data.message || '',
          created_at: latestJobRef.current?.created_at || new Date().toISOString(),
          updated_at: data.updated_at,
          completed_at: data.completed_at,
          api_endpoint_path: data.api_endpoint_path,
          sample_data: latestJobRef.current?.sample_data,
          error_info: latestJobRef.current?.error_info,
          analysis: latestJobRef.current?.analysis,
        };

        setJob(jobUpdate);
        latestJobRef.current = jobUpdate;
        onUpdate?.(jobUpdate);

        // Close connection if job is complete
        if (data.status === 'ready' || data.status === 'failed') {
          eventSource.close();
          onComplete?.();
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to parse update';
        setError(errorMessage);
        onError?.(errorMessage);
      }
    };

  eventSource.onerror = () => {
      if (!mountedRef.current) return;
      
      setError('SSE connection failed, falling back to polling');
      setIsConnected(false);
      eventSource.close();
      
      // Fallback to polling
      setUsePolling(true);
      startPolling();
    };

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [jobId, onUpdate, onError, onComplete, startPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  return {
    job,
    isConnected,
    error,
    usePolling,
    reconnect: () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  };
}
