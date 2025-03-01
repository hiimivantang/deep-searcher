import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Paper, Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, useTheme } from '@mui/material';

const MarkdownRenderer = ({ content }) => {
  const theme = useTheme();
  
  return (
    <Paper 
      elevation={2} 
      className="markdown-content"
      sx={{ 
        padding: 3, 
        borderRadius: 2,
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
      }}
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
          // Table components
          table: ({ node, ...props }) => {
            return (
              <Box sx={{ my: 3, borderRadius: '6px', overflow: 'hidden', border: `1px solid ${theme.palette.divider}` }}>
                <TableContainer 
                  sx={{ 
                    maxWidth: '100%', 
                    overflowX: 'auto',
                    backgroundColor: theme.palette.background.paper === '#262626' 
                      ? '#1a1a1a' 
                      : theme.palette.background.paper
                  }}
                >
                  <Table size="small" {...props} />
                </TableContainer>
              </Box>
            );
          },
          thead: ({ node, ...props }) => (
            <TableHead {...props} sx={{ 
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(0, 98, 255, 0.08)' 
                : 'rgba(0, 98, 255, 0.04)' 
            }} />
          ),
          tbody: ({ node, ...props }) => <TableBody {...props} />,
          tr: ({ node, ...props }) => <TableRow 
            {...props} 
            sx={{ 
              '&:nth-of-type(odd)': {
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.02)' 
                  : 'rgba(0, 0, 0, 0.02)'
              },
              '&:hover': {
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.04)' 
                  : 'rgba(0, 0, 0, 0.04)'
              }
            }} 
          />,
          th: ({ node, ...props }) => (
            <TableCell 
              {...props} 
              sx={{ 
                fontWeight: 'bold', 
                fontFamily: theme.typography.code.fontFamily,
                padding: '12px 16px',
                color: theme.palette.primary.main,
                borderBottom: `2px solid ${theme.palette.divider}`,
              }}
            />
          ),
          td: ({ node, ...props }) => (
            <TableCell 
              {...props} 
              sx={{ 
                padding: '10px 16px',
                borderBottom: `1px solid ${theme.palette.divider}`,
                fontFamily: theme.typography.code.fontFamily,
              }}
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
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(0, 0, 0, 0.3)' : 'rgba(0, 0, 0, 0.03)',
                    borderRadius: '6px',
                    padding: 2,
                    overflowX: 'auto',
                    fontFamily: theme.typography.code.fontFamily,
                    fontSize: '0.875rem',
                    color: theme.palette.text.primary,
                    whiteSpace: 'pre',
                    my: 2,
                    border: `1px solid ${theme.palette.divider}`,
                  }}
                >
                  {String(children)}
                </Box>
              );
            }
            
            return !inline && match ? (
              <Box sx={{ 
                borderRadius: '6px', 
                overflow: 'hidden', 
                my: 2,
                boxShadow: '0 3px 15px rgba(0, 0, 0, 0.2)',
                border: `1px solid ${theme.palette.divider}`,
                position: 'relative'
              }}>
                <Box sx={{ 
                  position: 'absolute', 
                  top: 0, 
                  right: 0, 
                  backgroundColor: 'rgba(0, 98, 255, 0.8)', 
                  color: 'white',
                  padding: '2px 8px',
                  borderBottomLeftRadius: '4px',
                  fontSize: '0.75rem',
                  fontFamily: theme.typography.code.fontFamily
                }}>
                  {match[1]}
                </Box>
                <SyntaxHighlighter
                  style={atomDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    padding: '16px',
                    borderRadius: 0,
                    backgroundColor: theme.palette.mode === 'dark' ? '#151718' : '#1E1E1E',
                  }}
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              </Box>
            ) : (
              <code 
                className={className} 
                style={{
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(0, 98, 255, 0.15)' : 'rgba(0, 98, 255, 0.08)',
                  padding: '2px 4px',
                  borderRadius: '3px',
                  color: theme.palette.mode === 'dark' ? '#c9d1d9' : '#24292e',
                  fontFamily: theme.typography.code.fontFamily,
                  fontWeight: 500,
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