import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import QueryPage from './components/QueryPage';
import LoadDataPage from './components/LoadDataPage';
import ConfigPage from './components/ConfigPage';
import AboutPage from './components/AboutPage';
import './App.css';

// Create a Carbon-inspired dark theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#0062ff', // Carbon blue
    },
    secondary: {
      main: '#3ddbd9', // Carbon teal
    },
    error: {
      main: '#fa4d56', // Carbon red
    },
    warning: {
      main: '#ff832b', // Carbon orange
    },
    success: {
      main: '#42be65', // Carbon green
    },
    background: {
      default: '#161616', // Carbon gray 100
      paper: '#262626',   // Carbon gray 90
    },
    text: {
      primary: '#f4f4f4', // Carbon white
      secondary: '#c6c6c6', // Carbon gray 10
    },
  },
  typography: {
    fontFamily: [
      'IBM Plex Sans',
      'Roboto',
      'Arial',
      'sans-serif',
    ].join(','),
    code: {
      fontFamily: [
        'IBM Plex Mono',
        'Menlo',
        'Monaco',
        'Courier New',
        'monospace',
      ].join(','),
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#161616', // Carbon gray 100
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        <Routes>
          <Route path="/" element={<QueryPage />} />
          <Route path="/load" element={<LoadDataPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  );
}

export default App;