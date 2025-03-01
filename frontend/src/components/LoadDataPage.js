import React, { useState } from 'react';
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
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Language as WebIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import axios from 'axios';

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
    severity: 'success'
  });

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
      });
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post('/load-files', {
        paths: validFilePaths.length === 1 ? validFilePaths[0] : validFilePaths,
        collection_name: fileCollectionName || undefined,
        collection_description: fileCollectionDescription || undefined,
      });
      
      setAlert({
        open: true,
        message: 'Files loaded successfully!',
        severity: 'success',
      });
      
      // Reset the form after successful submission
      setFilePaths(['']);
      setFileCollectionName('');
      setFileCollectionDescription('');
      
    } catch (error) {
      console.error('Error loading files:', error);
      setAlert({
        open: true,
        message: error.response?.data?.detail || 'Failed to load files. Please try again.',
        severity: 'error',
      });
    } finally {
      setLoading(false);
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
    setAlert({...alert, open: false});
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Load Data
      </Typography>
      
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
        autoHideDuration={6000} 
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseAlert} 
          severity={alert.severity} 
          sx={{ width: '100%' }}
        >
          {alert.message}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default LoadDataPage;