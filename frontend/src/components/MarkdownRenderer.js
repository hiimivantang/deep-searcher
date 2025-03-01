import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Paper, Typography, Box } from '@mui/material';

const MarkdownRenderer = ({ content }) => {
  return (
    <Paper 
      elevation={2} 
      className="markdown-content"
      sx={{ padding: 3, borderRadius: 2 }}
    >
      <ReactMarkdown
        components={{
          h1: ({ node, ...props }) => <Typography variant="h4" gutterBottom {...props} />,
          h2: ({ node, ...props }) => <Typography variant="h5" gutterBottom {...props} />,
          h3: ({ node, ...props }) => <Typography variant="h6" gutterBottom {...props} />,
          p: ({ node, ...props }) => <Typography variant="body1" paragraph {...props} />,
          a: ({ node, ...props }) => <a style={{ color: '#1976d2', textDecoration: 'none' }} {...props} />,
          pre: ({ node, ...props }) => (
            <Box 
              component="pre"
              sx={{ 
                backgroundColor: '#f5f5f5',
                borderRadius: 1,
                padding: 2,
                overflowX: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                color: '#333',
                borderLeft: '4px solid #1976d2',
                my: 2
              }}
              {...props}
            />
          ),
          code: ({ node, inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');
            const isAsciiArt = String(children).includes('│') || 
                               String(children).includes('┌') || 
                               String(children).includes('└') ||
                               String(children).includes('─') ||
                               String(children).includes('├') ||
                               String(children).includes('+--') ||
                               String(children).includes('|  ');
            
            if (isAsciiArt) {
              return (
                <Box 
                  component="pre"
                  sx={{ 
                    backgroundColor: '#f8f9fa',
                    borderRadius: 1,
                    padding: 2,
                    overflowX: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    color: '#333',
                    whiteSpace: 'pre',
                    my: 2
                  }}
                >
                  {String(children)}
                </Box>
              );
            }
            
            return !inline && match ? (
              <SyntaxHighlighter
                style={materialLight}
                language={match[1]}
                PreTag="div"
                customStyle={{
                  borderRadius: '4px',
                  padding: '16px',
                  backgroundColor: '#f5f7f9',
                  color: '#333',
                }}
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code 
                className={className} 
                style={{
                  backgroundColor: '#f0f0f0',
                  padding: '2px 4px',
                  borderRadius: '3px',
                  color: '#333',
                  fontFamily: 'monospace'
                }}
                {...props}
              >
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </Paper>
  );
};

export default MarkdownRenderer;