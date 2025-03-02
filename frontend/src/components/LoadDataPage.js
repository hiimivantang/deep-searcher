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
  Language as WebIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import axios from 'axios';

// Simple loading indicator - completely static, no WebSocket or async code
const LoadingIndicator = ({ loading }) => {
  if (!loading) return null;
  
  return (
    <Box sx={{ my: 3, p: 3, border: '1px solid #e0e0e0', borderRadius: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <CircularProgress size={20} sx={{ mr: 2 }} />
        <Typography>Processing your request. This may take a few minutes.</Typography>
      </Box>
      <LinearProgress sx={{ mt: 2 }} />
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
            
            // Reset processed files tracking for next upload
            setProcessedFiles(new Set());
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
      
      <LoadingIndicator loading={loading} />
      
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