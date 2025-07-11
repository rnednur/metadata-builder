import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiUtils, metadataAPI } from '../services/api';

const JobContext = createContext();

export const useJobs = () => {
  const context = useContext(JobContext);
  if (!context) {
    throw new Error('useJobs must be used within a JobProvider');
  }
  return context;
};

export const JobProvider = ({ children }) => {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const JOBS_STORAGE_KEY = 'metadata_generation_jobs';
  const POLLING_INTERVAL = 2000; // 2 seconds
  const activePollers = new Set(); // Track active polling operations

  // Storage utilities
  const saveJobsToStorage = (jobsList) => {
    try {
      localStorage.setItem(JOBS_STORAGE_KEY, JSON.stringify(jobsList));
    } catch (error) {
      console.warn('Failed to save jobs to localStorage:', error);
    }
  };

  const loadJobsFromStorage = () => {
    try {
      const stored = localStorage.getItem(JOBS_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn('Failed to load jobs from localStorage:', error);
      return [];
    }
  };

  const cleanupOldJobs = () => {
    const currentJobs = loadJobsFromStorage();
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    
    // Keep only jobs from the last 24 hours or running/pending jobs
    const cleanedJobs = currentJobs.filter(job => {
      const jobDate = new Date(job.startTime);
      return jobDate > oneDayAgo || job.status === 'running' || job.status === 'pending';
    });
    
    if (cleanedJobs.length !== currentJobs.length) {
      console.log(`Cleaned up ${currentJobs.length - cleanedJobs.length} old jobs`);
      saveJobsToStorage(cleanedJobs);
      return cleanedJobs;
    }
    return currentJobs;
  };

  // Initialize jobs from storage
  useEffect(() => {
    const cleanedJobs = cleanupOldJobs();
    if (cleanedJobs.length > 0) {
      console.log('JobContext: Restored jobs from storage:', cleanedJobs);
      setJobs(cleanedJobs);
      
      // Resume polling for any running jobs
      cleanedJobs.forEach(job => {
        if (job.jobId && (job.status === 'running' || job.status === 'pending')) {
          console.log(`JobContext: Resuming polling for job ${job.jobId}`);
          startPolling(job.jobId);
        }
      });
    }
  }, []);

  // Save jobs to storage whenever jobs state changes
  useEffect(() => {
    if (jobs.length > 0) {
      saveJobsToStorage(jobs);
    } else {
      // Clear storage if no jobs
      localStorage.removeItem(JOBS_STORAGE_KEY);
    }
  }, [jobs]);

  // Polling function
  const startPolling = async (jobId) => {
    if (activePollers.has(jobId)) {
      console.log(`Already polling job ${jobId}`);
      return;
    }
    
    activePollers.add(jobId);
    console.log(`Starting polling for job ${jobId}`);
    
    try {
      await apiUtils.pollJobStatus(
        jobId,
        (updatedJob) => {
          console.log(`Job ${jobId} status update:`, updatedJob);
          
          setJobs(prev => {
            const updatedJobs = prev.map(job => 
              job.jobId === jobId 
                ? {
                    ...job,
                    status: updatedJob.status,
                    progress: updatedJob.status === 'completed' ? 100 : (updatedJob.progress || 0),
                    duration: Math.floor((new Date() - new Date(job.startTime)) / 1000), // Duration in seconds
                    tableProgress: job.tableProgress.map(table => ({
                      ...table,
                      status: updatedJob.status,
                      progress: updatedJob.status === 'completed' ? 100 : (updatedJob.progress || 0)
                    })),
                    result: updatedJob.result,
                    error: updatedJob.error
                  }
                : job
            );
            console.log(`Updated jobs list for ${jobId}:`, updatedJobs);
            return updatedJobs;
          });

          // Dispatch metadata generation event when job completes
          if (updatedJob.status === 'completed') {
            setJobs(currentJobs => {
              const currentJob = currentJobs.find(j => j.jobId === jobId);
              if (currentJob && currentJob.tableProgress[0]) {
                const database = currentJob.tableProgress[0].database;
                const schema = currentJob.tableProgress[0].schema;
                const table = currentJob.tableProgress[0].name;
                
                const refreshEvent = new CustomEvent('metadataGenerated', {
                  detail: { database, schema, table }
                });
                window.dispatchEvent(refreshEvent);
                console.log(`Dispatched metadataGenerated event for ${database}.${schema}.${table}`);
              }
              return currentJobs;
            });
          }
          
          // Stop polling when job finishes
          if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
            activePollers.delete(jobId);
            console.log(`Stopped polling for job ${jobId}`);
          }
        },
        POLLING_INTERVAL,
        100 // max attempts
      );
    } catch (err) {
      console.error(`Polling failed for job ${jobId}:`, err);
      activePollers.delete(jobId);
      
      setJobs(prev => prev.map(job => 
        job.jobId === jobId 
          ? {
              ...job,
              status: 'failed',
              error: apiUtils.handleApiError(err)
            }
          : job
      ));
    }
  };

  // Job management functions
  const addJob = (jobData) => {
    console.log('Adding job to context:', jobData);
    setJobs(prev => [jobData, ...prev]);
    
    // Start polling if job has an ID and is active
    if (jobData.jobId && (jobData.status === 'running' || jobData.status === 'pending')) {
      startPolling(jobData.jobId);
    }
  };

  const removeJob = (jobId) => {
    setJobs(prev => prev.filter(job => job.jobId !== jobId && job.id !== jobId));
    activePollers.delete(jobId);
  };

  const updateJobWithRealId = (tempId, realJobData) => {
    setJobs(prev => prev.map(job => 
      job.id === tempId 
        ? {
            ...job,
            id: realJobData.job_id,
            jobId: realJobData.job_id,
            status: realJobData.status || 'running',
            logs: [
              ...job.logs,
              { 
                timestamp: new Date().toLocaleTimeString(), 
                level: 'info', 
                message: `Job submitted successfully: ${realJobData.job_id}` 
              }
            ]
          }
        : job
    ));
    
    // Start polling for the real job
    if (realJobData.job_id) {
      startPolling(realJobData.job_id);
    }
  };

  const updateJobStatus = (jobId, updates) => {
    setJobs(prev => prev.map(job => 
      (job.id === jobId || job.jobId === jobId)
        ? { ...job, ...updates }
        : job
    ));
  };

  const clearCompletedJobs = () => {
    setJobs(prev => {
      const runningJobs = prev.filter(job => job.status === 'running' || job.status === 'pending');
      
      // Stop polling for jobs we're removing
      prev.forEach(job => {
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          activePollers.delete(job.jobId);
        }
      });
      
      return runningJobs;
    });
  };

  const getJobsByStatus = (status) => {
    return jobs.filter(job => job.status === status);
  };

  const getJobStats = () => {
    const total = jobs.length;
    const completed = jobs.filter(job => job.status === 'completed').length;
    const running = jobs.filter(job => job.status === 'running').length;
    const failed = jobs.filter(job => job.status === 'failed').length;
    const pending = jobs.filter(job => job.status === 'pending').length;
    
    return { total, completed, running, failed, pending };
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      activePollers.clear();
    };
  }, []);

  const value = {
    jobs,
    isLoading,
    addJob,
    removeJob,
    updateJobWithRealId,
    updateJobStatus,
    clearCompletedJobs,
    getJobsByStatus,
    getJobStats,
    // Read-only getters
    totalJobs: jobs.length,
    hasActiveJobs: jobs.some(job => job.status === 'running' || job.status === 'pending'),
    completedJobs: jobs.filter(job => job.status === 'completed').length,
    failedJobs: jobs.filter(job => job.status === 'failed').length
  };

  return (
    <JobContext.Provider value={value}>
      {children}
    </JobContext.Provider>
  );
};

export default JobContext;