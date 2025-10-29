import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { RequireAuth } from './RequireAuth';
import { useUI } from '@/context/UIContext';

// Pages
import LandingPage from '@/pages/LandingPage';
import SignupPage from '@/pages/SignupPage';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import SellerPage from '@/pages/SellerPage';
import ProfilePage from '@/pages/ProfilePage';
import OrderHistoryPage from '@/pages/OrderHistoryPage';
import WishlistPage from '@/pages/WishlistPage';
import CartPage from '@/pages/CartPage';
import NotFoundPage from '@/pages/NotFoundPage';
import { ArtworkDetailPage } from '@/pages/ArtworkDetailPage';
import { AboutPage } from '@/pages/AboutPage';
import { ContactPage } from '@/pages/ContactPage';
import { ArtistPage } from '@/pages/ArtistPage';
import FestiveSpecialPage from '@/pages/FestiveSpecialPage';
import GiftServicePage from '@/pages/GiftServicePage';

export const AppRoutes = () => {
  const { mode } = useUI();

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<MainLayout><LandingPage /></MainLayout>} />
      <Route path="/signup" element={<MainLayout><SignupPage /></MainLayout>} />
      <Route path="/login" element={<MainLayout><LoginPage /></MainLayout>} />
      <Route path="/about" element={<MainLayout><AboutPage /></MainLayout>} />
      <Route path="/contact" element={<MainLayout><ContactPage /></MainLayout>} />
      
      {/* Protected routes - Main app route switches based on mode */}
      <Route 
        path="/dashboard" 
        element={
          <RequireAuth>
            <MainLayout>
              {mode === 'customer' ? <DashboardPage /> : <SellerPage />}
            </MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/artwork/:id" 
        element={
          <RequireAuth>
            <MainLayout><ArtworkDetailPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/artist/:artistId" 
        element={
          <RequireAuth>
            <MainLayout><ArtistPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/seller" 
        element={
          <RequireAuth>
            <MainLayout><SellerPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/profile" 
        element={
          <RequireAuth>
            <MainLayout><ProfilePage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/orders" 
        element={
          <RequireAuth>
            <MainLayout><OrderHistoryPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/wishlist" 
        element={
          <RequireAuth>
            <MainLayout><WishlistPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/cart" 
        element={
          <RequireAuth>
            <MainLayout><CartPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/festive-special" 
        element={
          <RequireAuth>
            <MainLayout><FestiveSpecialPage /></MainLayout>
          </RequireAuth>
        } 
      />

      <Route 
        path="/gift-ai" 
        element={
          <MainLayout>
            <GiftServicePage />
          </MainLayout>
        } 
      />
      
      {/* Catch all route */}
      <Route path="*" element={<MainLayout><NotFoundPage /></MainLayout>} />
    </Routes>
  );
};