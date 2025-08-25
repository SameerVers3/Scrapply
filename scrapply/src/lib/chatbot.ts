// Chatbot helper functions for parsing natural language commands

import { createScrapingRequest, listJobs, deleteJob, retryJob } from './api';

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isAnimated?: boolean;
}

export interface ChatCommand {
  type: 'create' | 'list' | 'delete' | 'retry' | 'help' | 'unknown';
  params: Record<string, unknown>;
}

// Parse natural language commands
export function parseCommand(message: string): ChatCommand {
  const lowerMessage = message.toLowerCase().trim();

  // Create scraper commands
  if (lowerMessage.includes('create scraper') || lowerMessage.includes('scrape')) {
    const urlMatch = message.match(/https?:\/\/[^\s]+/);
    const url = urlMatch ? urlMatch[0] : '';
    
    // Extract description from the message
    let description = message.replace(/create scraper for|scrape/i, '').replace(url, '').trim();
    if (!description) {
      description = 'Extract data from the website';
    }

    return {
      type: 'create',
      params: { url, description }
    };
  }

  // List jobs commands
  if (lowerMessage.includes('list') && (lowerMessage.includes('job') || lowerMessage.includes('scraper'))) {
    let status: string | undefined;
    
    if (lowerMessage.includes('ready')) status = 'ready';
    else if (lowerMessage.includes('pending')) status = 'pending';
    else if (lowerMessage.includes('failed')) status = 'failed';
    else if (lowerMessage.includes('running') || lowerMessage.includes('processing')) status = 'analyzing';

    return {
      type: 'list',
      params: { status }
    };
  }

  // Delete job commands
  if (lowerMessage.includes('delete') && lowerMessage.includes('job')) {
    const jobIdMatch = message.match(/job\s+(\w+)/i);
    const jobId = jobIdMatch ? jobIdMatch[1] : '';
    
    return {
      type: 'delete',
      params: { jobId }
    };
  }

  // Retry job commands
  if (lowerMessage.includes('retry') && lowerMessage.includes('job')) {
    const jobIdMatch = message.match(/job\s+(\w+)/i);
    const jobId = jobIdMatch ? jobIdMatch[1] : '';
    
    return {
      type: 'retry',
      params: { jobId }
    };
  }

  // Help command
  if (lowerMessage.includes('help') || lowerMessage.includes('commands')) {
    return {
      type: 'help',
      params: {}
    };
  }

  return {
    type: 'unknown',
    params: {}
  };
}

// Execute parsed commands
export async function executeCommand(command: ChatCommand): Promise<string> {
  try {
    switch (command.type) {
      case 'create':
        const { url, description } = command.params;
        if (!url || typeof url !== 'string') {
          return 'Please provide a valid URL to scrape.';
        }
        
        if (!description || typeof description !== 'string') {
          return 'Please provide a description for the scraping job.';
        }
        
        const job = await createScrapingRequest({ url, description });
        return `✅ Created scraping job for ${url}. Job ID: ${job.id}. Status: ${job.status}`;

      case 'list':
        const { status } = command.params;
        const statusStr = typeof status === 'string' ? status : undefined;
        const jobs = await listJobs(10, 0, statusStr);
        
        if (jobs.jobs.length === 0) {
          return statusStr ? `No jobs found with status: ${statusStr}` : 'No jobs found.';
        }

        const jobList = jobs.jobs.map(job => 
          `• ${job.id}: ${job.url} (${job.status})`
        ).join('\n');
        
        return `📋 Jobs:\n${jobList}`;

      case 'delete':
        const { jobId: deleteJobId } = command.params;
        if (!deleteJobId || typeof deleteJobId !== 'string') {
          return 'Please provide a job ID to delete.';
        }
        
        await deleteJob(deleteJobId);
        return `🗑️ Deleted job ${deleteJobId}.`;

      case 'retry':
        const { jobId: retryJobId } = command.params;
        if (!retryJobId || typeof retryJobId !== 'string') {
          return 'Please provide a job ID to retry.';
        }
        
        const retriedJob = await retryJob(retryJobId);
        return `🔄 Retrying job ${retryJobId}. New status: ${retriedJob.status}`;

      case 'help':
        return `🤖 Available commands:
• "Create scraper for https://example.com" - Create a new scraping job
• "List jobs" - Show all jobs
• "List ready jobs" - Show only ready jobs
• "Delete job [ID]" - Delete a specific job
• "Retry job [ID]" - Retry a failed job
• "Help" - Show this help message`;

      case 'unknown':
        return 'I didn\'t understand that command. Type "help" to see available commands.';

      default:
        return 'Unknown command type.';
    }
  } catch (error) {
    return `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
  }
}

// Generate a unique message ID
export function generateMessageId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}
