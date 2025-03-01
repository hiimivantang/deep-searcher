import React, { useState } from 'react';
import { 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  Box, 
  CircularProgress,
  Slider,
  FormControl,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Switch
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';
import MarkdownRenderer from './MarkdownRenderer';

const QueryPage = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [maxIter, setMaxIter] = useState(3);
  const [error, setError] = useState('');
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState('');
  const [useAdvancedQuery, setUseAdvancedQuery] = useState(true);

  React.useEffect(() => {
    // Fetch available collections when component mounts
    const fetchCollections = async () => {
      try {
        const response = await axios.get('/collections');
        if (response.data && Array.isArray(response.data)) {
          setCollections(response.data);
          if (response.data.length > 0) {
            setSelectedCollection(response.data[0]);
          }
        } else {
          console.warn('Collections response is not an array:', response.data);
          setCollections([]);
        }
      } catch (err) {
        console.error('Failed to fetch collections:', err);
        setCollections([]);
        // Don't show error to user, just use empty collections
      }
    };

    fetchCollections();
  }, []);

  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  const handleMaxIterChange = (event, newValue) => {
    setMaxIter(newValue);
  };

  const handleCollectionChange = (event) => {
    setSelectedCollection(event.target.value);
  };

  const handleToggleQueryMode = () => {
    setUseAdvancedQuery(!useAdvancedQuery);
  };

  const handleQuerySubmit = async (event) => {
    event.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }
    
    setError('');
    setLoading(true);
    setResult('');
    
    try {
      let response;
      
      if (useAdvancedQuery) {
        // Advanced query with reflection and sub-queries
        response = await axios.get('/query', {
          params: {
            original_query: query,
            max_iter: maxIter
          }
        });
      } else {
        // Simple RAG query
        response = await axios.get('/naive-query', {
          params: {
            query: query,
            collection: selectedCollection || undefined
          }
        });
      }
      
      setResult(response.data.result || 'No results found');
    } catch (error) {
      console.error('Error submitting query:', error);
      setError('Failed to get results. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Search Knowledge Base
      </Typography>
      
      <Paper 
        elevation={3}
        component="form"
        onSubmit={handleQuerySubmit}
        sx={{ p: 3, mb: 4 }}
      >
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              variant="outlined"
              label="Enter your query"
              value={query}
              onChange={handleQueryChange}
              margin="normal"
              multiline
              rows={3}
              error={!!error}
              helperText={error}
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch 
                  checked={useAdvancedQuery} 
                  onChange={handleToggleQueryMode} 
                  color="primary"
                />
              }
              label={useAdvancedQuery ? "Using advanced query with reflection" : "Using simple RAG query"}
            />
          </Grid>
          
          {useAdvancedQuery ? (
            <Grid item xs={12} md={6}>
              <Typography id="max-iter-slider" gutterBottom>
                Max Iterations: {maxIter}
              </Typography>
              <Slider
                value={maxIter}
                onChange={handleMaxIterChange}
                aria-labelledby="max-iter-slider"
                valueLabelDisplay="auto"
                step={1}
                marks
                min={1}
                max={5}
              />
            </Grid>
          ) : (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="collection-select-label">Collection</InputLabel>
                <Select
                  labelId="collection-select-label"
                  value={selectedCollection}
                  label="Collection"
                  onChange={handleCollectionChange}
                >
                  <MenuItem value="">
                    <em>All Collections</em>
                  </MenuItem>
                  {collections.map((collection) => (
                    <MenuItem key={collection} value={collection}>
                      {collection}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
          
          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              startIcon={<SearchIcon />}
              disabled={loading}
            >
              Search
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {result && !loading && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Results
          </Typography>
          
          {/* Wrap content in triple backticks if it contains ASCII art but isn't already formatted as markdown */}
          <MarkdownRenderer 
            content={
              (result.includes('│') || result.includes('┌') || result.includes('└') || 
               result.includes('─') || result.includes('├') || result.includes('+--') || 
               result.includes('|  ')) && 
              !result.includes('```') ? 
              '```\n' + result + '\n```' : 
              result
            } 
          />
        </Box>
      )}
    </div>
  );
};

export default QueryPage;