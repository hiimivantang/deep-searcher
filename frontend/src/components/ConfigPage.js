import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Snackbar,
  Alert,
  CircularProgress,
  Slider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import axios from 'axios';

const ConfigPage = () => {
  const [config, setConfig] = useState({
    provide_settings: {
      llm: {
        provider: '',
        config: {}
      },
      embedding: {
        provider: '',
        config: {}
      },
      file_loader: {
        provider: '',
        config: {}
      },
      web_crawler: {
        provider: '',
        config: {}
      },
      vector_db: {
        provider: '',
        config: {}
      }
    },
    query_settings: {
      max_iter: 3
    },
    load_settings: {
      chunk_size: 1500,
      chunk_overlap: 100
    }
  });
  
  const [loading, setLoading] = useState(false);
  const [fetchingConfig, setFetchingConfig] = useState(true);
  const [alert, setAlert] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  
  // Provider options
  const llmProviders = ['OpenAI', 'Bedrock', 'DeepSeek', 'Gemini', 'Grok', 'SiliconFlow', 'TogetherAI'];
  const embeddingProviders = ['OpenAIEmbedding', 'BedrockEmbedding', 'VoyageEmbedding', 'MilvusEmbedding'];
  const fileLoaderProviders = ['PDFLoader', 'TextLoader', 'JSONLoader', 'UnstructuredLoader'];
  const webCrawlerProviders = ['FireCrawlCrawler', 'JinaCrawler', 'Crawl4AICrawler'];
  const vectorDbProviders = ['Milvus'];
  
  useEffect(() => {
    // Fetch configuration when component mounts
    const fetchConfig = async () => {
      try {
        const response = await axios.get('/config');
        if (response.data && response.data.provide_settings) {
          setConfig(response.data);
        } else {
          console.warn('Invalid config format received:', response.data);
          setAlert({
            open: true,
            message: 'Invalid configuration format received. Using default values.',
            severity: 'warning',
          });
        }
      } catch (err) {
        console.error('Failed to fetch configuration:', err);
        setAlert({
          open: true,
          message: 'Failed to load configuration. Using default values.',
          severity: 'warning',
        });
      } finally {
        setFetchingConfig(false);
      }
    };
    
    fetchConfig();
  }, []);
  
  const handleProviderChange = (feature, provider) => {
    setConfig({
      ...config,
      provide_settings: {
        ...config.provide_settings,
        [feature]: {
          ...config.provide_settings[feature],
          provider: provider,
          // Reset config when provider changes
          config: {}
        }
      }
    });
  };
  
  const handleConfigChange = (feature, key, value) => {
    setConfig({
      ...config,
      provide_settings: {
        ...config.provide_settings,
        [feature]: {
          ...config.provide_settings[feature],
          config: {
            ...config.provide_settings[feature].config,
            [key]: value
          }
        }
      }
    });
  };
  
  const handleQuerySettingChange = (key, value) => {
    setConfig({
      ...config,
      query_settings: {
        ...config.query_settings,
        [key]: value
      }
    });
  };
  
  const handleLoadSettingChange = (key, value) => {
    setConfig({
      ...config,
      load_settings: {
        ...config.load_settings,
        [key]: value
      }
    });
  };
  
  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post('/update-config', config);
      setAlert({
        open: true,
        message: 'Configuration updated successfully!',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error updating configuration:', error);
      setAlert({
        open: true,
        message: error.response?.data?.detail || 'Failed to update configuration.',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleCloseAlert = () => {
    setAlert({...alert, open: false});
  };
  
  if (fetchingConfig) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Configuration
      </Typography>
      
      <form onSubmit={handleSubmit}>
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Provider Settings
          </Typography>
          
          {/* LLM Settings */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">LLM Provider</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Provider</InputLabel>
                    <Select
                      value={config.provide_settings.llm.provider}
                      onChange={(e) => handleProviderChange('llm', e.target.value)}
                      label="Provider"
                    >
                      {llmProviders.map(provider => (
                        <MenuItem key={provider} value={provider}>{provider}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                {config.provide_settings.llm.provider && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 1 }}>Provider Configuration</Divider>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Model"
                        value={config.provide_settings.llm.config.model || ''}
                        onChange={(e) => handleConfigChange('llm', 'model', e.target.value)}
                        placeholder="e.g., gpt-4o, amazon.nova-lite-v1:0"
                      />
                    </Grid>
                    
                    {['OpenAI'].includes(config.provide_settings.llm.provider) && (
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="API Key"
                          value={config.provide_settings.llm.config.api_key || ''}
                          onChange={(e) => handleConfigChange('llm', 'api_key', e.target.value)}
                          type="password"
                        />
                      </Grid>
                    )}
                    
                    {['Bedrock', 'BedrockEmbedding'].includes(config.provide_settings.llm.provider) && (
                      <>
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="AWS Access Key ID"
                            value={config.provide_settings.llm.config.aws_access_key_id || ''}
                            onChange={(e) => handleConfigChange('llm', 'aws_access_key_id', e.target.value)}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="AWS Secret Access Key"
                            value={config.provide_settings.llm.config.aws_secret_access_key || ''}
                            onChange={(e) => handleConfigChange('llm', 'aws_secret_access_key', e.target.value)}
                            type="password"
                          />
                        </Grid>
                      </>
                    )}
                  </>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* Embedding Settings */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Embedding Provider</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Provider</InputLabel>
                    <Select
                      value={config.provide_settings.embedding.provider}
                      onChange={(e) => handleProviderChange('embedding', e.target.value)}
                      label="Provider"
                    >
                      {embeddingProviders.map(provider => (
                        <MenuItem key={provider} value={provider}>{provider}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                {config.provide_settings.embedding.provider && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 1 }}>Provider Configuration</Divider>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Model"
                        value={config.provide_settings.embedding.config.model || ''}
                        onChange={(e) => handleConfigChange('embedding', 'model', e.target.value)}
                        placeholder="e.g., text-embedding-3-large"
                      />
                    </Grid>
                    
                    {['OpenAIEmbedding'].includes(config.provide_settings.embedding.provider) && (
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="API Key"
                          value={config.provide_settings.embedding.config.api_key || ''}
                          onChange={(e) => handleConfigChange('embedding', 'api_key', e.target.value)}
                          type="password"
                        />
                      </Grid>
                    )}
                    
                    {['BedrockEmbedding'].includes(config.provide_settings.embedding.provider) && (
                      <>
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="AWS Access Key ID"
                            value={config.provide_settings.embedding.config.aws_access_key_id || ''}
                            onChange={(e) => handleConfigChange('embedding', 'aws_access_key_id', e.target.value)}
                          />
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="AWS Secret Access Key"
                            value={config.provide_settings.embedding.config.aws_secret_access_key || ''}
                            onChange={(e) => handleConfigChange('embedding', 'aws_secret_access_key', e.target.value)}
                            type="password"
                          />
                        </Grid>
                      </>
                    )}
                  </>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* Vector DB Settings */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Vector Database</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Provider</InputLabel>
                    <Select
                      value={config.provide_settings.vector_db.provider}
                      onChange={(e) => handleProviderChange('vector_db', e.target.value)}
                      label="Provider"
                    >
                      {vectorDbProviders.map(provider => (
                        <MenuItem key={provider} value={provider}>{provider}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                {config.provide_settings.vector_db.provider === 'Milvus' && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 1 }}>Provider Configuration</Divider>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="URI"
                        value={config.provide_settings.vector_db.config.uri || ''}
                        onChange={(e) => handleConfigChange('vector_db', 'uri', e.target.value)}
                        placeholder="e.g., https://your-milvus-endpoint.com:19538"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Token"
                        value={config.provide_settings.vector_db.config.token || ''}
                        onChange={(e) => handleConfigChange('vector_db', 'token', e.target.value)}
                        type="password"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Default Collection"
                        value={config.provide_settings.vector_db.config.default_collection || ''}
                        onChange={(e) => handleConfigChange('vector_db', 'default_collection', e.target.value)}
                        placeholder="e.g., deepsearcher"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Database"
                        value={config.provide_settings.vector_db.config.db || ''}
                        onChange={(e) => handleConfigChange('vector_db', 'db', e.target.value)}
                        placeholder="e.g., default"
                      />
                    </Grid>
                  </>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* File Loader and Web Crawler Settings */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">File Loader & Web Crawler</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>File Loader</InputLabel>
                    <Select
                      value={config.provide_settings.file_loader.provider}
                      onChange={(e) => handleProviderChange('file_loader', e.target.value)}
                      label="File Loader"
                    >
                      {fileLoaderProviders.map(provider => (
                        <MenuItem key={provider} value={provider}>{provider}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Web Crawler</InputLabel>
                    <Select
                      value={config.provide_settings.web_crawler.provider}
                      onChange={(e) => handleProviderChange('web_crawler', e.target.value)}
                      label="Web Crawler"
                    >
                      {webCrawlerProviders.map(provider => (
                        <MenuItem key={provider} value={provider}>{provider}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* Query and Loading Settings */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Advanced Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Typography id="max-iter-slider" gutterBottom>
                    Max Iterations: {config.query_settings.max_iter}
                  </Typography>
                  <Slider
                    value={config.query_settings.max_iter}
                    onChange={(e, newValue) => handleQuerySettingChange('max_iter', newValue)}
                    aria-labelledby="max-iter-slider"
                    valueLabelDisplay="auto"
                    step={1}
                    marks
                    min={1}
                    max={5}
                  />
                  <FormHelperText>
                    Maximum number of reflection iterations during search
                  </FormHelperText>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Chunk Size"
                    type="number"
                    value={config.load_settings.chunk_size}
                    onChange={(e) => handleLoadSettingChange('chunk_size', parseInt(e.target.value))}
                    inputProps={{ min: 100, max: 5000 }}
                  />
                  <FormHelperText>
                    Size of document chunks (in characters)
                  </FormHelperText>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Chunk Overlap"
                    type="number"
                    value={config.load_settings.chunk_overlap}
                    onChange={(e) => handleLoadSettingChange('chunk_overlap', parseInt(e.target.value))}
                    inputProps={{ min: 0, max: 500 }}
                  />
                  <FormHelperText>
                    Overlap between document chunks (in characters)
                  </FormHelperText>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <SaveIcon />}
              disabled={loading}
              size="large"
            >
              {loading ? 'Saving...' : 'Save Configuration'}
            </Button>
          </Box>
        </Paper>
      </form>
      
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

export default ConfigPage;