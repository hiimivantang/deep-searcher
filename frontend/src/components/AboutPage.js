import React from 'react';
import { 
  Typography, 
  Paper, 
  Box, 
  Grid, 
  Divider, 
  Link,
  Card,
  CardContent,
  CardMedia
} from '@mui/material';

const AboutPage = () => {
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        About DeepSearcher
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Overview
          </Typography>
          <Typography variant="body1" paragraph>
            DeepSearcher is an advanced search and retrieval system designed to process, index, and search through large amounts of data with high precision. 
            It combines vector search capabilities with iterative refinement to provide comprehensive answers to complex queries.
          </Typography>
          
          <Typography variant="body1" paragraph>
            The system uses a combination of state-of-the-art language models, embedding techniques, and vector databases to enable semantic search across your knowledge base.
          </Typography>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Architecture
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
            <img 
              src="/assets/pic/deep-searcher-arch.png" 
              alt="DeepSearcher Architecture" 
              style={{ maxWidth: '100%', height: 'auto' }}
              onError={(e) => { e.target.src = 'https://via.placeholder.com/800x400?text=Architecture+Diagram'; }}
            />
          </Box>
          
          <Typography variant="body1" paragraph>
            DeepSearcher consists of several components:
          </Typography>
          
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Data Loading
                  </Typography>
                  <Typography variant="body2">
                    Supports loading from local files and web crawling. Documents are chunked and embedded for efficient retrieval.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Vector Database
                  </Typography>
                  <Typography variant="body2">
                    Stores document embeddings for semantic similarity search using Milvus.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Query Processing
                  </Typography>
                  <Typography variant="body2">
                    Breaks down complex queries into sub-queries and uses iterative refinement to find the most relevant information.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Answer Generation
                  </Typography>
                  <Typography variant="body2">
                    Synthesizes retrieved information into comprehensive answers using advanced language models.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box>
          <Typography variant="h5" gutterBottom>
            Supported Providers
          </Typography>
          
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Language Models
              </Typography>
              <ul>
                <li>OpenAI (GPT-4, GPT-3.5)</li>
                <li>Amazon Bedrock</li>
                <li>DeepSeek</li>
                <li>Google Gemini</li>
                <li>Grok</li>
                <li>TogetherAI</li>
                <li>SiliconFlow</li>
              </ul>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Embedding Models
              </Typography>
              <ul>
                <li>OpenAI Embeddings</li>
                <li>Amazon Bedrock Embeddings</li>
                <li>Voyage AI Embeddings</li>
                <li>Milvus Embeddings</li>
              </ul>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Loaders & Crawlers
              </Typography>
              <ul>
                <li>PDF Loader</li>
                <li>Text Loader</li>
                <li>JSON Loader</li>
                <li>Unstructured Loader</li>
                <li>FireCrawl Crawler</li>
                <li>Jina Crawler</li>
                <li>Crawl4AI Crawler</li>
              </ul>
            </Grid>
          </Grid>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            &copy; {new Date().getFullYear()} DeepSearcher. All rights reserved.
          </Typography>
          <Typography variant="body2" color="textSecondary">
            <Link href="https://github.com/your-repo/deep-searcher" target="_blank" rel="noopener">
              GitHub Repository
            </Link>
          </Typography>
        </Box>
      </Paper>
    </div>
  );
};

export default AboutPage;