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
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Polling fallback function
  const startPolling = useCallback(() => {
    if (!jobId || !mountedRef.current) return;
    
    console.log('📊 Starting polling fallback for job:', jobId);
    setUsePolling(true);
    
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
    
    // Set up polling interval (reduced to 2 seconds since SSE failed)
    pollingIntervalRef.current = setInterval(poll, 2000);
  }, [jobId, onUpdate, onError, onComplete]);

  const connectSSE = useCallback(() => {
    if (!jobId || typeof window === 'undefined') return;

    console.log('🔌 Attempting SSE connection for job:', jobId);
    
    // Close existing connections
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const eventSource = new EventSource(`${API_BASE_URL}/api/v1/scraping/jobs/stream/${jobId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      if (mountedRef.current) {
        console.log('✅ SSE connection established for job:', jobId);
        setIsConnected(true);
        setError(null);
        setUsePolling(false);
        reconnectAttemptsRef.current = 0;
      }
    };

    eventSource.onmessage = (e) => {
      if (!mountedRef.current) return;
      
      try {
        const data = JSON.parse(e.data);
        
        // Handle different message types
        if (data.type === 'keepalive') {
          console.log('💓 SSE keepalive received');
          return;
        }
        
        if (data.error) {
          console.error('❌ SSE error received:', data.error);
          setError(data.error);
          onError?.(data.error);
          
          // If final error, close connection and fallback to polling
          if (data.final) {
            eventSource.close();
            startPolling();
          }
          return;
        }

        // Convert the stream data to JobResponse format, preserving original job data
        const jobUpdate: JobResponse = {
          id: data.id,
          url: latestJobRef.current?.url || data.url || '',
          description: latestJobRef.current?.description || data.description || '',
          status: data.status,
          progress: data.progress || 0,
          message: data.message || '',
          created_at: latestJobRef.current?.created_at || data.created_at || new Date().toISOString(),
          updated_at: data.updated_at || new Date().toISOString(),
          completed_at: data.completed_at || latestJobRef.current?.completed_at,
          api_endpoint_path: data.api_endpoint_path || latestJobRef.current?.api_endpoint_path,
          sample_data: data.sample_data || latestJobRef.current?.sample_data,
          error_info: data.error_info || latestJobRef.current?.error_info,
          analysis: data.analysis || latestJobRef.current?.analysis,
        };

        console.log('📦 SSE update received:', {
          status: jobUpdate.status,
          progress: jobUpdate.progress,
          message: jobUpdate.message,
          preservedUrl: jobUpdate.url,
          preservedDescription: jobUpdate.description
        });

        setJob(jobUpdate);
        // Only update latestJobRef with the new data, preserving existing fields
        latestJobRef.current = {
          ...latestJobRef.current,
          ...jobUpdate
        };
        onUpdate?.(jobUpdate);

        // Close connection if job is complete or marked as final
        if (data.final || data.status === 'ready' || data.status === 'failed') {
          console.log('🏁 Job completed, closing SSE connection');
          eventSource.close();
          onComplete?.();
          return; // Prevent further reconnection attempts
        }
        
        // Handle connection closing messages
        if (data.type === 'connection_closing') {
          console.log('📡 Server closing SSE connection:', data.reason);
          eventSource.close();
          if (data.reason === 'job_completed') {
            onComplete?.();
          }
          return; // Prevent reconnection for completed jobs
        }
      } catch (err) {
        console.error('❌ Failed to parse SSE data:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to parse update';
        setError(errorMessage);
        onError?.(errorMessage);
      }
    };

    eventSource.onerror = (event) => {
      if (!mountedRef.current) return;
      
      console.error('❌ SSE connection error for job:', jobId);
      setIsConnected(false);
      
      // Don't retry for completed jobs
      if (latestJobRef.current && 
          (latestJobRef.current.status === 'ready' || latestJobRef.current.status === 'failed')) {
        console.log('🚫 Not retrying SSE for completed job');
        eventSource.close();
        return;
      }
      
      // Check if we should retry or fallback to polling
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        console.log(`🔄 Retrying SSE connection (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
        
        // Close current connection
        eventSource.close();
        
        // Retry after a delay
        setTimeout(() => {
          if (mountedRef.current) {
            connectSSE();
          }
        }, 2000 * reconnectAttemptsRef.current); // Exponential backoff
      } else {
        console.log('🚫 Max SSE retry attempts reached, falling back to polling');
        setError('SSE connection failed, using polling fallback');
        eventSource.close();
        startPolling();
      }
    };
  }, [jobId, onUpdate, onError, onComplete, startPolling]);

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

    // If we have a job and it's already completed, avoid unnecessary SSE connections
    if (latestJobRef.current && 
        (latestJobRef.current.status === 'ready' || latestJobRef.current.status === 'failed')) {
      console.log('📋 Job already completed, skipping SSE connection');
      return;
    }

    // Start SSE connection
    connectSSE();

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
  }, [jobId, connectSSE]);

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

  const reconnect = useCallback(() => {
    console.log('🔄 Manual reconnect requested');
    reconnectAttemptsRef.current = 0; // Reset retry counter
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    connectSSE();
  }, [connectSSE]);

  return {
    job,
    isConnected,
    error,
    usePolling,
    reconnect
  };
}
