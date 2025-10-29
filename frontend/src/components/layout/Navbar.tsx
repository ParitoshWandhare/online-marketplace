import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Menu, User, LogOut, Package, Heart, ShoppingBag, ShoppingCart, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useAuth } from '@/context/AuthContext';
import { useUI } from '@/context/UIContext';
import { cartService } from '@/services/cart';
import { toast } from 'sonner';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const { mode, setMode } = useUI();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [cartItemCount, setCartItemCount] = useState(0);

  // Fetch cart item count
  useEffect(() => {
    if (user) {
      fetchCartItemCount();
    } else {
      setCartItemCount(0);
    }
  }, [user]);

  const fetchCartItemCount = async () => {
    try {
      const response = await cartService.getCart();
      if (response.success && response.cart) {
        const itemCount = response.cart.items.reduce((sum: number, item: any) => sum + item.qty, 0);
        setCartItemCount(itemCount);
      } else {
        setCartItemCount(0);
      }
    } catch (error) {
      console.error('Error fetching cart:', error);
      toast.error('Failed to load cart data');
      setCartItemCount(0);
    }
  };

  // CMD/CTRL + K for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('search-input') as HTMLInputElement;
        searchInput?.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const toggleMode = () => {
    const newMode = mode === 'customer' ? 'seller' : 'customer';
    setMode(newMode);
    navigate('/dashboard');
  };

  const NavContent = () => (
    <>
      {user && (
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Label htmlFor="mode-toggle" className="text-sm">
              {mode === 'customer' ? 'Customer' : 'Seller'}
            </Label>
            <Switch
              id="mode-toggle"
              checked={mode === 'seller'}
              onCheckedChange={toggleMode}
            />
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.avatarUrl} alt={user.name} />
                  <AvatarFallback>{user.name.charAt(0).toUpperCase()}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 bg-background" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user.name}</p>
                  <p className="text-xs leading-none text-muted-foreground">{user.email}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/profile')}>
                <User className="mr-2 h-4 w-4" />
                <span>View Profile</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/orders')}>
                <Package className="mr-2 h-4 w-4" />
                <span>Order History</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/wishlist')}>
                <Heart className="mr-2 h-4 w-4" />
                <span>Wishlist</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/cart')}>
                <ShoppingCart className="mr-2 h-4 w-4" />
                <span>Cart {cartItemCount > 0 && `(${cartItemCount})`}</span>
              </DropdownMenuItem>
              {mode === 'seller' && (
                <DropdownMenuItem onClick={() => navigate('/seller')}>
                  <ShoppingBag className="mr-2 h-4 w-4" />
                  <span>Seller Dashboard</span>
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      {!user && (
        <div className="flex items-center space-x-2">
          <Button variant="ghost" onClick={() => navigate('/login')}>
            Log in
          </Button>
          <Button onClick={() => navigate('/signup')} className="btn-gradient">
            Sign up
          </Button>
        </div>
      )}
    </>
  );

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary-glow rounded-lg flex items-center justify-center">
            <ShoppingBag className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="font-bold text-xl">ORCHID</span>
        </Link>

        {/* Search - Desktop */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <form onSubmit={handleSearch} className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              id="search-input"
              type="text"
              placeholder="Search products... (Command K)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4"
            />
          </form>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-8">
          <Link
            to="/dashboard"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Explore
          </Link>

          {/* GIFT AI LINK */}
          <Link
            to="/gift-ai"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Gift AI
          </Link>

          <a href="/about" className="text-muted-foreground hover:text-foreground transition-colors">
            About
          </a>
          <a href="/contact" className="text-muted-foreground hover:text-foreground transition-colors">
            Contact
          </a>
        </nav>

        {/* Desktop User Actions */}
        <div className="hidden md:flex">
          <NavContent />
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <div className="flex flex-col space-y-6 mt-8">

                {/* Mobile Search */}
                <form onSubmit={handleSearch} className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    type="text"
                    placeholder="Search products..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4"
                  />
                </form>

                {/* Mobile Nav Links */}
                <div className="flex flex-col space-y-3">
                  <Link to="/dashboard" className="text-lg font-medium hover:text-purple-600">
                    Explore
                  </Link>

                  {/* GIFT AI IN MOBILE */}
                  <Link to="/gift-ai" className="text-lg font-medium hover:text-purple-600">
                    Gift AI
                  </Link>

                  <a href="/about" className="text-lg font-medium text-muted-foreground hover:text-foreground">
                    About
                  </a>
                  <a href="/contact" className="text-lg font-medium text-muted-foreground hover:text-foreground">
                    Contact
                  </a>
                </div>

                <NavContent />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
};