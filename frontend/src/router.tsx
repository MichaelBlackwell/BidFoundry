import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout';
import {
  NewDocumentPage,
  HistoryPage,
  CompanyProfilesPage,
  SettingsPage,
  GenerationPage,
  DocumentViewPage,
} from './pages';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell><Navigate to="/new" replace /></AppShell>,
  },
  {
    path: '/new',
    element: <AppShell><NewDocumentPage /></AppShell>,
  },
  {
    path: '/history',
    element: <AppShell><HistoryPage /></AppShell>,
  },
  {
    path: '/profiles',
    element: <AppShell><CompanyProfilesPage /></AppShell>,
  },
  {
    path: '/settings',
    element: <AppShell><SettingsPage /></AppShell>,
  },
  {
    path: '/generate/:requestId',
    element: <AppShell><GenerationPage /></AppShell>,
  },
  {
    path: '/documents/:id',
    element: <AppShell><DocumentViewPage /></AppShell>,
  },
]);
