import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Edit, Mail, Phone, Calendar, MapPin, Plus, Trash2, Check } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { format } from 'date-fns';
import { EditProfileForm } from '@/components/forms/EditProfileForm';
import { AddAddressForm } from '@/components/forms/AddAddressForm';
import { likeService } from '@/services/like';
import { userService, Address } from '@/services/user';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';

const ProfilePage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [isAddingAddress, setIsAddingAddress] = useState(false);
  const [wishlistCount, setWishlistCount] = useState(0);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [isLoadingAddresses, setIsLoadingAddresses] = useState(true);

  useEffect(() => {
    const fetchWishlistCount = async () => {
      try {
        const response = await likeService.getLikedArtworks();
        setWishlistCount(response.count);
      } catch (error) {
        console.error('Failed to fetch wishlist count');
      }
    };

    fetchWishlistCount();
  }, []);

  useEffect(() => {
    const fetchAddresses = async () => {
      try {
        const response = await userService.getAddresses();
        setAddresses(response.addresses);
      } catch (error) {
        console.error('Failed to fetch addresses');
        toast({
          title: 'Error',
          description: 'Failed to load addresses',
          variant: 'destructive',
        });
      } finally {
        setIsLoadingAddresses(false);
      }
    };

    fetchAddresses();
  }, [toast]);

  const handleSetDefaultAddress = async (addressId: string) => {
    try {
      await userService.setDefaultAddress(addressId);
      setAddresses(addresses.map(addr => ({
        ...addr,
        isDefault: addr._id === addressId
      })));
      toast({
        title: 'Success',
        description: 'Default address updated',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to set default address',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteAddress = async (addressId: string) => {
    try {
      await userService.deleteAddress(addressId);
      setAddresses(addresses.filter(addr => addr._id !== addressId));
      toast({
        title: 'Success',
        description: 'Address deleted successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete address',
        variant: 'destructive',
      });
    }
  };

  const handleAddAddress = async (addressData: any) => {
    try {
      const response = await userService.addAddress(addressData);
      setAddresses([...addresses, response.address]);
      setIsAddingAddress(false);
      toast({
        title: 'Success',
        description: 'Address added successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add address',
        variant: 'destructive',
      });
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Profile Header */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              <Avatar className="w-24 h-24">
                <AvatarImage src={user.avatarUrl} alt={user.name} />
                <AvatarFallback className="text-2xl">
                  {user.name.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1">
                <div className="flex flex-col md:flex-row md:items-center gap-4 mb-4">
                  <h1 className="text-3xl font-bold">{user.name}</h1>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    {user.email}
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4" />
                    {user.phone}
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Joined {format(new Date(user.createdAt), 'MMMM yyyy')}
                  </div>
                </div>
                
                {user.bio && (
                  <p className="mt-4 text-muted-foreground">{user.bio}</p>
                )}
              </div>
              
              <Dialog open={isEditing} onOpenChange={setIsEditing}>
                <Button
                  onClick={() => setIsEditing(true)}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Edit className="w-4 h-4" />
                  Edit Profile
                </Button>
                <DialogContent className="max-w-md" aria-describedby="">
                  <DialogHeader>
                    <DialogTitle>Edit Profile</DialogTitle>
                  </DialogHeader>
                  <EditProfileForm onSuccess={() => setIsEditing(false)} />
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>

        {/* Shipping Addresses Section */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Shipping Addresses
              </CardTitle>
              <Button 
                size="sm" 
                className="flex items-center gap-2"
                onClick={() => setIsAddingAddress(true)}
              >
                <Plus className="w-4 h-4" />
                Add Address
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingAddresses ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading addresses...
              </div>
            ) : addresses.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No addresses added yet. Add your first shipping address.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {addresses.map((address) => (
                  <Card key={address._id} className="relative">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Badge variant={address.isDefault ? "default" : "secondary"}>
                            {address.label}
                          </Badge>
                          {address.isDefault && (
                            <Badge variant="outline" className="flex items-center gap-1">
                              <Check className="w-3 h-3" />
                              Default
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8"
                            onClick={() => handleDeleteAddress(address._id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="space-y-1 text-sm">
                        <p className="font-semibold">{address.fullName}</p>
                        <p className="text-muted-foreground">{address.addressLine1}</p>
                        {address.addressLine2 && (
                          <p className="text-muted-foreground">{address.addressLine2}</p>
                        )}
                        {address.landmark && (
                          <p className="text-muted-foreground">Landmark: {address.landmark}</p>
                        )}
                        <p className="text-muted-foreground">
                          {address.city}, {address.state} - {address.pincode}
                        </p>
                        <p className="text-muted-foreground">{address.country}</p>
                        <p className="text-muted-foreground">Phone: {address.phone}</p>
                      </div>
                      
                      {!address.isDefault && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-4 w-full"
                          onClick={() => handleSetDefaultAddress(address._id)}
                        >
                          Set as Default
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Add Address Dialog */}
        <Dialog open={isAddingAddress} onOpenChange={setIsAddingAddress}>
          <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Address</DialogTitle>
            </DialogHeader>
            <AddAddressForm onSuccess={handleAddAddress} />
          </DialogContent>
        </Dialog>

        {/* Profile Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stats Cards */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">+2 this month</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Wishlist Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{wishlistCount}</div>
              <p className="text-xs text-muted-foreground">Items you've liked</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Reviews Written</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">5</div>
              <p className="text-xs text-muted-foreground">4.8 avg rating</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;