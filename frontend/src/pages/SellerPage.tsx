import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Package, ShoppingCart, BarChart } from 'lucide-react';
import { userService } from '@/services/user';
import { useToast } from '@/hooks/use-toast';
import { NewPostForm } from '@/components/forms/NewPostForm';
import { InventoryTable } from '@/components/seller/InventoryTable';
import { OrdersTable } from '@/components/seller/OrdersTable';
import { Loader } from '@/components/ui/Loader';

const SellerPage = () => {
  const [activeTab, setActiveTab] = useState('new-post');
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalOrders: 0,
    totalRevenue: 0,
  });
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSellerStats();
  }, []);

  const loadSellerStats = async () => {
    try {
      const response = await userService.getSellerStats();
      if (response.success) {
        setStats(response.stats);
      }
    } catch (error) {
      console.error('Error loading seller stats:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load seller statistics.',
      });
    } finally {
      setLoading(false);
    }
  };

  const statsCards = [
    {
      title: 'Total Products',
      value: stats.totalProducts.toString(),
      icon: Package,
      description: 'Products added in the last 30 days',
    },
    {
      title: 'Total Orders',
      value: stats.totalOrders.toString(),
      icon: ShoppingCart,
      description: 'Orders received in the last 30 days',
    },
    {
      title: 'Revenue',
      value: `₹${stats.totalRevenue.toFixed(2)}`,
      icon: BarChart,
      description: 'Revenue generated in the last 30 days',
    },
  ];

  if (loading) {
    return <Loader text="Loading seller dashboard..." />;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Seller Dashboard</h1>
          <p className="text-muted-foreground">
            Manage your products, orders, and grow your business
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {statsCards.map((stat, index) => (
            <Card key={index} className="group hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 gap-4 bg-muted p-1 rounded-md">
            <TabsTrigger value="new-post" className="flex items-center justify-center gap-2 py-2">
              <Plus className="w-4 h-4" />
              New Post
            </TabsTrigger>
            <TabsTrigger value="orders" className="flex items-center justify-center py-2">
              Orders
            </TabsTrigger>
            <TabsTrigger value="inventory" className="flex items-center justify-center py-2">
              Inventory
            </TabsTrigger>
          </TabsList>

          {/* New Post */}
          <TabsContent value="new-post" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Create New Product</CardTitle>
              </CardHeader>
              <CardContent>
                <NewPostForm />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Orders */}
          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Order Management</CardTitle>
              </CardHeader>
              <CardContent>
                <OrdersTable /> {/* ✅ using your existing component */}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Inventory */}
          <TabsContent value="inventory" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Product Inventory</CardTitle>
              </CardHeader>
              <CardContent>
                <InventoryTable />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SellerPage;
