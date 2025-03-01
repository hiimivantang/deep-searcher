import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Container,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  useTheme,
  alpha
} from '@mui/material';
import { 
  Menu as MenuIcon,
  Search as SearchIcon,
  Storage as StorageIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
  ChevronLeft as ChevronLeftIcon,
  Code as CodeIcon
} from '@mui/icons-material';

const drawerWidth = 240;

const Layout = ({ children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const menuItems = [
    { text: 'Query', icon: <SearchIcon />, path: '/' },
    { text: 'Load Data', icon: <StorageIcon />, path: '/load' },
    { text: 'Configuration', icon: <SettingsIcon />, path: '/config' },
    { text: 'About', icon: <InfoIcon />, path: '/about' }
  ];

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleNavigation = (path) => {
    navigate(path);
    setDrawerOpen(false);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: theme.palette.background.default,
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
          borderBottom: `1px solid ${theme.palette.divider}`
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CodeIcon 
              sx={{ 
                color: theme.palette.primary.main, 
                mr: 1.5, 
                fontSize: '2rem' 
              }} 
            />
            <Typography 
              variant="h6" 
              noWrap 
              component="div" 
              sx={{ 
                fontWeight: 600,
                letterSpacing: '0.5px',
                background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              DeepSearcher
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="temporary"
        open={drawerOpen}
        onClose={handleDrawerToggle}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            backgroundColor: theme.palette.background.default,
            borderRight: `1px solid ${theme.palette.divider}`,
          },
        }}
      >
        <Box 
          sx={{ 
            p: 2, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            bgcolor: 'rgba(0, 0, 0, 0.05)',
            borderBottom: `1px solid ${theme.palette.divider}`
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CodeIcon 
              sx={{ 
                color: theme.palette.primary.main, 
                mr: 1, 
                fontSize: '1.5rem' 
              }} 
            />
            <Typography 
              variant="subtitle1" 
              sx={{ 
                fontWeight: 600,
                background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Navigation
            </Typography>
          </Box>
          <IconButton 
            onClick={handleDrawerToggle}
            size="small"
            sx={{ 
              color: theme.palette.text.secondary,
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.08),
              }
            }}
          >
            <ChevronLeftIcon />
          </IconButton>
        </Box>
        <List sx={{ p: 1 }}>
          {menuItems.map((item) => {
            const isSelected = location.pathname === item.path;
            return (
              <ListItem 
                button 
                key={item.text} 
                onClick={() => handleNavigation(item.path)}
                selected={isSelected}
                sx={{
                  borderRadius: '8px',
                  mb: 0.5,
                  color: isSelected ? theme.palette.primary.main : theme.palette.text.primary,
                  bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.08) : 'transparent',
                  '&:hover': {
                    bgcolor: isSelected 
                      ? alpha(theme.palette.primary.main, 0.12)
                      : alpha(theme.palette.primary.main, 0.04)
                  },
                  '& .MuiListItemIcon-root': {
                    color: isSelected ? theme.palette.primary.main : theme.palette.text.primary,
                  }
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  primaryTypographyProps={{ 
                    fontWeight: isSelected ? 600 : 400,
                  }} 
                />
              </ListItem>
            );
          })}
        </List>
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 4 },
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: theme.palette.background.default,
          backgroundImage: theme.palette.mode === 'dark' 
            ? 'radial-gradient(circle at 25% 25%, rgba(0, 98, 255, 0.04) 0%, transparent 20%), radial-gradient(circle at 75% 75%, rgba(61, 219, 217, 0.04) 0%, transparent 20%)'
            : 'none',
          backgroundSize: '100% 100%',
          backgroundAttachment: 'fixed',
        }}
      >
        <Toolbar /> {/* This is needed for spacing below the AppBar */}
        <Container 
          maxWidth="lg"
          sx={{ 
            pt: 3, 
            pb: 6,
            animation: 'fadeIn 0.5s ease-out',
            '@keyframes fadeIn': {
              '0%': {
                opacity: 0,
                transform: 'translateY(10px)'
              },
              '100%': {
                opacity: 1,
                transform: 'translateY(0)'
              }
            }
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;