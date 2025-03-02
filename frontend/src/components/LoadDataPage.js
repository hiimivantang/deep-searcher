import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Grid,
  Tabs,
  Tab,
  Snackbar,
  Alert,
  CircularProgress,
  Divider,
  Chip,
  LinearProgress,
  Card,
  CardContent,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CloudUpload,
  Language as WebIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCut,
  Memory,
  Storage,
} from '@mui/icons-material';
import axios from 'axios';

// Enable this for debugging progress issues
const DEBUG_PROGRESS = true;

// Enhanced loading indicator with dynamic progress updates
const LoadingIndicator = ({ loading, progressData }) => {
  if (!loading) return null;
  
  // Find relevant tasks for each stage with improved matching logic
  const findTaskByType = (type) => {
    const allTasks = Object.entries(progressData || {});
    
    // Look for most recent update first
    let mostRecent = null;
    let mostRecentTime = 0;
    
    for (const [id, task] of allTasks) {
      // If type matches what we're looking for
      if (task && task.type === type) {
        // If task has a timestamp and it's more recent
        if (task.timestamp && task.timestamp > mostRecentTime) {
          mostRecent = task;
          mostRecentTime = task.timestamp;
        }
        // If no timestamp but we haven't found anything yet
        else if (!mostRecent) {
          mostRecent = task;
        }
      }
    }
    
    // Return the most recent task of this type
    if (mostRecent) {
      if (DEBUG_PROGRESS) {
        console.log(`Found ${type} task with ${mostRecent.percentage}% progress`);
      }
      return mostRecent;
    }
    
    // Nothing found
    return null;
  };
  
  // Get tasks for each stage with improved lookup
  const loadingTask = findTaskByType('loading');
  const chunkingTask = findTaskByType('chunking');
  const embeddingTask = findTaskByType('embedding');
  const storingTask = findTaskByType('storing');
  
  // Calculate default values for missing stages based on completed stages
  const getDefaultPercentage = (stageIndex) => {
    const stages = [loadingTask, chunkingTask, embeddingTask, storingTask];
    
    // Debug the stage values
    if (DEBUG_PROGRESS) {
      console.log(`Stage ${stageIndex} check:`, stages[stageIndex]);
    }
    
    // If this stage has explicit progress, use it
    if (stages[stageIndex]?.percentage !== undefined) {
      if (DEBUG_PROGRESS) {
        console.log(`  Using explicit percentage: ${stages[stageIndex].percentage}%`);
      }
      return stages[stageIndex].percentage;
    }
    
    // Find the last stage with progress
    for (let i = stageIndex-1; i >= 0; i--) {
      if (stages[i]?.percentage !== undefined && stages[i].percentage === 100) {
        // Previous stage is complete, so we're starting
        const result = stageIndex === i+1 ? 5 : 0; // 5% progress if we're the next stage
        if (DEBUG_PROGRESS) {
          console.log(`  Previous stage ${i} complete, returning ${result}%`);
        }
        return result;
      }
    }
    
    // If loading has started, we should show at least loading at 100%
    if (stageIndex === 0) {
      if (DEBUG_PROGRESS) {
        console.log(`  First stage, defaulting to 100%`);
      }
      return 100;
    }
    
    if (DEBUG_PROGRESS) {
      console.log(`  No progress info, returning 0%`);
    }
    return 0;
  };
  
  // Function to render stage progress
  const renderStage = (title, task, icon, stageIndex) => {
    // If task exists, it's active; otherwise check if previous stage is complete
    const active = !!task || (stageIndex > 0 && getDefaultPercentage(stageIndex-1) === 100);
    
    // Use task percentage if available, otherwise use default based on progress
    const percentage = task?.percentage !== undefined ? task.percentage : getDefaultPercentage(stageIndex);
    
    const message = task?.message || '';
    
    return (
      <Box sx={{ mb: 2, opacity: active ? 1 : 0.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          {icon}
          <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: active ? 'bold' : 'normal' }}>
            {title}
          </Typography>
          {active && (
            <Typography variant="caption" sx={{ ml: 'auto', color: 'text.secondary' }}>
              {percentage.toFixed(1)}%
            </Typography>
          )}
        </Box>
        <LinearProgress 
          variant={active ? "determinate" : "indeterminate"} 
          value={percentage}
          sx={{ height: 6, borderRadius: 1 }}
        />
        {active && message && (
          <Typography variant="caption" sx={{ display: 'block', mt: 0.5, fontSize: '0.7rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {message}
          </Typography>
        )}
      </Box>
    );
  };
  
  // Check if we have any task data at all
  const hasAnyTask = loadingTask || chunkingTask || embeddingTask || storingTask;
  
  return (
    <Box sx={{ my: 3, p: 3, border: '1px solid #e0e0e0', borderRadius: 1 }}>
      <Typography variant="h6" gutterBottom>
        Processing Progress
      </Typography>
      
      {!hasAnyTask && (
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <CircularProgress size={20} sx={{ mr: 2 }} />
          <Typography>Starting processing... Please wait.</Typography>
        </Box>
      )}
      
      <Box sx={{ mt: 3 }}>
        {renderStage("File Loading", loadingTask, <CloudUpload fontSize="small" color={loadingTask ? "primary" : "disabled"} />, 0)}
        {renderStage("Text Chunking", chunkingTask, <ContentCut fontSize="small" color={chunkingTask ? "primary" : "disabled"} />, 1)}
        {renderStage("Embedding Generation", embeddingTask, <Memory fontSize="small" color={embeddingTask ? "primary" : "disabled"} />, 2)}
        {renderStage("Database Storage", storingTask, <Storage fontSize="small" color={storingTask ? "primary" : "disabled"} />, 3)}
      </Box>
      
      <Typography variant="caption" sx={{ display: 'block', mt: 2, color: 'text.secondary' }}>
        This process may take several minutes depending on the size of your files.
        {!hasAnyTask && " If you don't see progress after 10-15 seconds, check Docker logs for possible issues."}
      </Typography>
    </Box>
  );
};

const LoadDataPage = () => {
  // State for file tab
  const [filePaths, setFilePaths] = useState(['']);
  const [fileCollectionName, setFileCollectionName] = useState('');
  const [fileCollectionDescription, setFileCollectionDescription] = useState('');
  
  // State for URL tab
  const [urls, setUrls] = useState(['']);
  const [urlCollectionName, setUrlCollectionName] = useState('');
  const [urlCollectionDescription, setUrlCollectionDescription] = useState('');
  
  // General state
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({
    open: false,
    message: '',
    severity: 'info',
    progress: 0
  });
  
  // Progress state
  const [progressData, setProgressData] = useState({});

  // Poll for progress updates
  // Track processed files to avoid duplicate notifications
  const [processedFiles, setProcessedFiles] = useState(new Set());
  
  // Poll for progress updates and show notifications for completed documents
  useEffect(() => {
    let pollInterval;
    
    if (loading) {
      // Set up polling interval to check for progress
      pollInterval = setInterval(async () => {
        try {
          const response = await axios.get('/progress');
          const progressData = response.data;
          
          // Detailed debugging of progress data (controlled by debug flag)
          if (DEBUG_PROGRESS) {
            console.log("Progress data received:", progressData);
            
            // Extract task-specific progress for debugging
            const loadingTask = Object.values(progressData || {}).find(task => task?.type === 'loading');
            const chunkingTask = Object.values(progressData || {}).find(task => task?.type === 'chunking');
            const embeddingTask = Object.values(progressData || {}).find(task => task?.type === 'embedding');
            const storingTask = Object.values(progressData || {}).find(task => task?.type === 'storing');
            
            // Log specifically embedding and storing progress
            if (embeddingTask) {
              console.log(`EMBEDDING PROGRESS: ${embeddingTask.percentage?.toFixed(1)}% - ${embeddingTask.message}`);
            }
            
            if (storingTask) {
              console.log(`STORING PROGRESS: ${storingTask.percentage?.toFixed(1)}% - ${storingTask.message}`);
            }
          }
          
          // Update the progress data state
          setProgressData(progressData);
          
          // Add debug info about missing tasks if needed
          if (DEBUG_PROGRESS) {
            const hasEmbedding = Object.values(progressData || {}).some(task => task?.type === 'embedding');
            const hasStoring = Object.values(progressData || {}).some(task => task?.type === 'storing');
            
            if (!hasEmbedding) {
              console.warn("⚠️ No embedding progress data found in response!");
            }
            
            if (!hasStoring) {
              console.warn("⚠️ No storing progress data found in response!");
            }
          }
          
          // Extract all tasks
          const tasks = Object.values(progressData);
          
          // Check for task completion
          const completeTask = tasks.find(task => task && task.type === 'complete');
          
          // Find tasks with loaded files
          for (const task of tasks) {
            if (task && Array.isArray(task.loaded_files) && task.loaded_files.length > 0) {
              // Show notifications for newly processed files
              task.loaded_files.forEach(file => {
                const fileId = `${file.path}-${file.count}`;
                if (!processedFiles.has(fileId)) {
                  setProcessedFiles(prev => new Set([...prev, fileId]));
                  
                  // Show a notification for this file
                  setAlert({
                    open: true,
                    message: `Processed: ${file.path} (${file.count} document${file.count !== 1 ? 's' : ''})`,
                    severity: 'info',
                    progress: task.percentage || 0
                  });
                  
                  // Auto-close after 3 seconds to prevent notification buildup
                  setTimeout(() => {
                    setAlert(prev => {
                      if (prev.message.includes(file.path)) {
                        return {...prev, open: false};
                      }
                      return prev;
                    });
                  }, 3000);
                }
              });
            }
          }
          
          // If complete task is found, finish the process
          if (completeTask) {
            // If we found a complete task, finish loading
            setLoading(false);
            setAlert({
              open: true,
              message: 'All documents processed successfully',
              severity: 'success',
              progress: 100
            });
            
            // Reset form fields after completion
            if (tabValue === 0) {
              setFilePaths(['']);
              setFileCollectionName('');
              setFileCollectionDescription('');
            }
            
            // Clear the polling interval
            clearInterval(pollInterval);
            
            // Reset progress data and processed files tracking for next upload
            setTimeout(() => {
              setProgressData({});
              setProcessedFiles(new Set());
            }, 3000); // Clear progress after 3 seconds to let user see the completion
          }
        } catch (error) {
          console.error('Error checking progress:', error);
        }
      }, 1500); // Check more frequently (every 1.5 seconds)
    }
    
    return () => {
      // Clean up interval on unmount or when loading state changes
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [loading, tabValue, processedFiles]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // File paths handlers
  const handleFilePathChange = (index, value) => {
    const newFilePaths = [...filePaths];
    newFilePaths[index] = value;
    setFilePaths(newFilePaths);
  };

  const addFilePath = () => {
    setFilePaths([...filePaths, '']);
  };

  const removeFilePath = (index) => {
    const newFilePaths = filePaths.filter((_, i) => i !== index);
    if (newFilePaths.length === 0) {
      newFilePaths.push('');
    }
    setFilePaths(newFilePaths);
  };

  // URL handlers
  const handleUrlChange = (index, value) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const addUrl = () => {
    setUrls([...urls, '']);
  };

  const removeUrl = (index) => {
    const newUrls = urls.filter((_, i) => i !== index);
    if (newUrls.length === 0) {
      newUrls.push('');
    }
    setUrls(newUrls);
  };

  const handleFileSubmit = async (event) => {
    event.preventDefault();
    
    // Filter out empty file paths
    const validFilePaths = filePaths.filter(path => path.trim() !== '');
    
    if (validFilePaths.length === 0) {
      setAlert({
        open: true,
        message: 'Please enter at least one valid file path',
        severity: 'error',
        progress: 0
      });
      return;
    }

    setLoading(true);
    setAlert({
      open: true,
      message: 'Starting file upload...',
      severity: 'info',
      progress: 0
    });
    
    try {
      await axios.post('/load-files', {
        paths: validFilePaths.length === 1 ? validFilePaths[0] : validFilePaths,
        collection_name: fileCollectionName || undefined,
        collection_description: fileCollectionDescription || undefined,
      });
      
      // Don't reset form yet - wait for completion in progress polling
      
    } catch (error) {
      console.error('Error loading files:', error);
      setLoading(false);
      setAlert({
        open: true,
        message: error.response?.data?.detail || 'Failed to load files. Please try again.',
        severity: 'error',
        progress: 0
      });
    }
  };

  const handleUrlSubmit = async (event) => {
    event.preventDefault();
    
    // Filter out empty URLs
    const validUrls = urls.filter(url => url.trim() !== '');
    
    if (validUrls.length === 0) {
      setAlert({
        open: true,
        message: 'Please enter at least one valid URL',
        severity: 'error',
      });
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post('/load-website', {
        urls: validUrls.length === 1 ? validUrls[0] : validUrls,
        collection_name: urlCollectionName || undefined,
        collection_description: urlCollectionDescription || undefined,
      });
      
      setAlert({
        open: true,
        message: 'Website(s) loaded successfully!',
        severity: 'success',
      });
      
      // Reset the form after successful submission
      setUrls(['']);
      setUrlCollectionName('');
      setUrlCollectionDescription('');
      
    } catch (error) {
      console.error('Error loading website:', error);
      setAlert({
        open: true,
        message: error.response?.data?.detail || 'Failed to load website. Please try again.',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseAlert = () => {
    // Only close alert if not loading
    if (!loading) {
      setAlert({...alert, open: false});
    }
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Load Data
      </Typography>
      
      <LoadingIndicator loading={loading} progressData={progressData} />
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            aria-label="data loading tabs"
          >
            <Tab label="Load Local Files" />
            <Tab label="Load from Website" />
          </Tabs>
        </Box>
        
        {/* Tab 1: Load Local Files */}
        {tabValue === 0 && (
          <form onSubmit={handleFileSubmit}>
            <Grid container spacing={3}>
              {filePaths.map((path, index) => (
                <Grid item xs={12} key={index} sx={{ display: 'flex', alignItems: 'center' }}>
                  <TextField
                    fullWidth
                    label={`File Path ${index + 1}`}
                    value={path}
                    onChange={(e) => handleFilePathChange(index, e.target.value)}
                    placeholder="Enter absolute file path or directory"
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  <Button 
                    color="error" 
                    onClick={() => removeFilePath(index)}
                    disabled={filePaths.length === 1}
                  >
                    <DeleteIcon />
                  </Button>
                </Grid>
              ))}
              
              <Grid item xs={12}>
                <Button 
                  startIcon={<AddIcon />} 
                  onClick={addFilePath}
                  variant="outlined"
                  sx={{ mb: 2 }}
                >
                  Add File Path
                </Button>
              </Grid>
              
              <Grid item xs={12}>
                <Divider>
                  <Chip label="Collection Information" />
                </Divider>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Collection Name (Optional)"
                  value={fileCollectionName}
                  onChange={(e) => setFileCollectionName(e.target.value)}
                  placeholder="Custom collection name"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Collection Description (Optional)"
                  value={fileCollectionDescription}
                  onChange={(e) => setFileCollectionDescription(e.target.value)}
                  placeholder="Brief description of this data"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <UploadIcon />}
                  disabled={loading}
                  size="large"
                >
                  {loading ? 'Loading...' : 'Load Files'}
                </Button>
              </Grid>
            </Grid>
          </form>
        )}
        
        {/* Tab 2: Load from Website */}
        {tabValue === 1 && (
          <form onSubmit={handleUrlSubmit}>
            <Grid container spacing={3}>
              {urls.map((url, index) => (
                <Grid item xs={12} key={index} sx={{ display: 'flex', alignItems: 'center' }}>
                  <TextField
                    fullWidth
                    label={`URL ${index + 1}`}
                    value={url}
                    onChange={(e) => handleUrlChange(index, e.target.value)}
                    placeholder="Enter website URL"
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  <Button 
                    color="error" 
                    onClick={() => removeUrl(index)}
                    disabled={urls.length === 1}
                  >
                    <DeleteIcon />
                  </Button>
                </Grid>
              ))}
              
              <Grid item xs={12}>
                <Button 
                  startIcon={<AddIcon />} 
                  onClick={addUrl}
                  variant="outlined"
                  sx={{ mb: 2 }}
                >
                  Add URL
                </Button>
              </Grid>
              
              <Grid item xs={12}>
                <Divider>
                  <Chip label="Collection Information" />
                </Divider>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Collection Name (Optional)"
                  value={urlCollectionName}
                  onChange={(e) => setUrlCollectionName(e.target.value)}
                  placeholder="Custom collection name"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Collection Description (Optional)"
                  value={urlCollectionDescription}
                  onChange={(e) => setUrlCollectionDescription(e.target.value)}
                  placeholder="Brief description of this data"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <WebIcon />}
                  disabled={loading}
                  size="large"
                >
                  {loading ? 'Loading...' : 'Load Website'}
                </Button>
              </Grid>
            </Grid>
          </form>
        )}
      </Paper>
      
      <Snackbar 
        open={alert.open} 
        autoHideDuration={loading ? null : 6000}  // Don't auto-hide final success message
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        key={alert.message} // Key helps React identify which snackbar to update
      >
        <Alert 
          onClose={handleCloseAlert}
          severity={alert.severity}
          sx={{ width: '100%', maxWidth: '500px' }} // Set a max width for better readability
        >
          <Box sx={{ width: '100%' }}>
            <Typography 
              variant="body2"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                // Only if the message is a file path, otherwise let it wrap
                whiteSpace: alert.message.includes('Processed:') ? 'nowrap' : 'normal',
                maxWidth: '460px'
              }}
            >
              {alert.message}
            </Typography>
            {alert.progress > 0 && (
              <Box sx={{ width: '100%', mt: 1 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={Math.min(100, alert.progress)} 
                  sx={{ 
                    height: 4, 
                    borderRadius: 2,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 2,
                    }
                  }}
                />
                <Typography variant="caption" sx={{ mt: 0.5, display: 'block', textAlign: 'right' }}>
                  {alert.progress.toFixed(1)}% Complete
                </Typography>
              </Box>
            )}
          </Box>
        </Alert>
      </Snackbar>
    </div>
  );
};

export default LoadDataPage;