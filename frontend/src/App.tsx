import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  ThemeProvider,
  AuthProvider,
  WebSocketProvider,
  AccessibilityProvider,
} from './providers';
import { router } from './router';
import { SkipLink } from './components/ui';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <AccessibilityProvider>
            <WebSocketProvider>
              <SkipLink targetId="main-content" />
              <RouterProvider router={router} />
            </WebSocketProvider>
          </AccessibilityProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
