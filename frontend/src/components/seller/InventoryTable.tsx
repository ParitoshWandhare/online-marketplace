import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Edit, Trash, Package, TrendingUp } from 'lucide-react';
import { artworkService, type Artwork } from '@/services/artwork';
import { visionAiService } from '@/services/visionAi';
import { useToast } from '@/hooks/use-toast';
import { Loader } from '@/components/ui/Loader';

export const InventoryTable = () => {
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingArtwork, setEditingArtwork] = useState<Artwork | null>(null);
  const [restockingArtwork, setRestockingArtwork] = useState<Artwork | null>(null);
  const [restockQuantity, setRestockQuantity] = useState(1);
  const [aiBoostingArtwork, setAiBoostingArtwork] = useState<Artwork | null>(null);
  const [aiBoostData, setAiBoostData] = useState<any>(null);
  const [aiBoostError, setAiBoostError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    price: 0,
    currency: '',
    quantity: 1,
    status: 'draft' as 'draft' | 'published' | 'out_of_stock'
  });
  const { toast } = useToast();

  useEffect(() => {
    const loadMyArtworks = async () => {
      try {
        const response = await artworkService.getMyArtworks();
        if (response.success && response.artworks) {
          setArtworks(response.artworks);
        }
      } catch (error) {
        console.error('Error loading artworks:', error);
        toast({ variant: 'destructive', title: 'Error', description: 'Failed to load your artworks.' });
      } finally {
        setLoading(false);
      }
    };
    loadMyArtworks();
  }, [toast]);

  const handleDelete = async (id: string) => {
    try {
      await artworkService.deleteArtwork(id);
      setArtworks(artworks.filter(artwork => artwork._id !== id));
      toast({ title: 'Success', description: 'Artwork deleted successfully.' });
    } catch (error) {
      console.error('Error deleting artwork:', error);
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete artwork.' });
    }
  };

  const getCurrencySymbol = (currency: string) => {
    const symbols: { [key: string]: string } = { INR: '₹', USD: '$', EUR: '€', GBP: '£' };
    return symbols[currency] || currency;
  };

  const handleEdit = (artwork: Artwork) => {
    setEditingArtwork(artwork);
    setEditForm({
      title: artwork.title,
      description: artwork.description || '',
      price: artwork.price,
      currency: artwork.currency,
      quantity: artwork.quantity,
      status: artwork.quantity === 0
        ? 'out_of_stock'
        : (['draft', 'published', 'out_of_stock'].includes(artwork.status)
          ? artwork.status as 'draft' | 'published' | 'out_of_stock'
          : 'draft')
    });
  };

  const handleUpdateArtwork = async () => {
    if (!editingArtwork) return;
    try {
      const updatedForm = {
        ...editForm,
        quantity: parseInt(String(editForm.quantity)),
        price: parseFloat(String(editForm.price)),
        status: editForm.quantity === 0 ? 'out_of_stock' : editForm.status
      };
      const response = await artworkService.updateArtwork(editingArtwork._id, updatedForm);
      if (response.success && response.artwork) {
        setArtworks(artworks.map(artwork => artwork._id === editingArtwork._id ? response.artwork! : artwork));
        setEditingArtwork(null);
        toast({ title: 'Success', description: 'Artwork updated successfully.' });
      }
    } catch (error) {
      console.error('Error updating artwork:', error);
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to update artwork. Only draft artworks can be edited.' });
    }
  };

  const handleRestock = async () => {
    if (!restockingArtwork || restockQuantity <= 0) return;
    try {
      const response = await artworkService.restockArtwork(restockingArtwork._id, restockQuantity);
      if (response.success && response.artwork) {
        setArtworks(artworks.map(artwork => artwork._id === restockingArtwork._id ? response.artwork! : artwork));
        setRestockingArtwork(null);
        setRestockQuantity(1);
        toast({ title: 'Success', description: 'Artwork restocked successfully.' });
      }
    } catch (error) {
      console.error('Error restocking artwork:', error);
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to restock artwork.' });
    }
  };

  const handleAiBoost = async (artwork: Artwork) => {
    setAiBoostingArtwork(artwork);
    setAiBoostData(null);
    setAiBoostError(null);

    try {
      const imageUrl = artwork.media?.[0]?.url;
      if (!imageUrl) throw new Error("No image found for artwork.");

      const response = await fetch(imageUrl);
      const imageBlob = await response.blob();

      const [purchaseResp, fulfillmentResp] = await Promise.all([
        visionAiService.purchaseAnalysis(imageBlob),
        visionAiService.orderFulfillment(imageBlob)
      ]);

      if (!purchaseResp.success && !fulfillmentResp.success) {
        throw new Error(purchaseResp.error || fulfillmentResp.error || "Unknown AI error");
      }

      setAiBoostData({
        cart_suggestions: purchaseResp.data?.cart_suggestions || [],
        purchase_analysis: purchaseResp.data?.purchase_analysis || '',
        packaging_suggestions: fulfillmentResp.data?.packaging_suggestions || [],
        shipping_considerations: fulfillmentResp.data?.shipping_considerations || ''
      });
    } catch (err: any) {
      console.error("AI Boost error:", err);
      setAiBoostError(err.message || "Failed to fetch AI Boost data");
    }
  };

  if (loading) return <Loader text="Loading your products..." />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>Price</TableHead>
          <TableHead>Quantity</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Likes</TableHead>
          <TableHead>Actions</TableHead>
          <TableHead>AI Boost</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {artworks.length === 0 ? (
          <TableRow>
            <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
              No products found. Create your first product!
            </TableCell>
          </TableRow>
        ) : (
          artworks.map(artwork => (
            <TableRow key={artwork._id}>
              <TableCell className="font-medium">{artwork.title}</TableCell>
              <TableCell>{getCurrencySymbol(artwork.currency)}{artwork.price}</TableCell>
              <TableCell>{artwork.quantity}</TableCell>
              <TableCell>
                <Badge variant={artwork.status === 'published' ? 'default' : artwork.status === 'out_of_stock' ? 'destructive' : 'secondary'}>
                  {artwork.status.replace('_', ' ')}
                </Badge>
              </TableCell>
              <TableCell>{artwork.likeCount}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  {/* Edit */}
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="sm" disabled={artwork.status !== 'draft'} onClick={() => handleEdit(artwork)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-md">
                      <DialogHeader>
                        <DialogTitle>Edit Artwork</DialogTitle>
                        <DialogDescription>Update product details here.</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="title">Title</Label>
                          <Input
                            id="title"
                            value={editForm.title}
                            onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label htmlFor="description">Description</Label>
                          <Textarea
                            id="description"
                            value={editForm.description}
                            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="price">Price</Label>
                            <Input
                              id="price"
                              type="number"
                              value={editForm.price}
                              onChange={(e) => setEditForm({ ...editForm, price: parseFloat(e.target.value) || 0 })}
                            />
                          </div>
                          <div>
                            <Label htmlFor="currency">Currency</Label>
                            <Input
                              id="currency"
                              value={editForm.currency}
                              onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                              placeholder="Enter currency code (e.g., USD, EUR)"
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="quantity">Quantity</Label>
                            <Input
                              id="quantity"
                              type="number"
                              min="0"
                              value={editForm.quantity}
                              onChange={(e) => setEditForm({ ...editForm, quantity: parseInt(e.target.value) || 0 })}
                            />
                          </div>
                          <div>
                            <Label htmlFor="status">Status</Label>
                            <Select
                              value={editForm.quantity === 0 ? 'out_of_stock' : editForm.status}
                              onValueChange={(value) => setEditForm({ ...editForm, status: value as 'draft' | 'published' | 'out_of_stock' })}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="draft">Draft</SelectItem>
                                <SelectItem value="published">Published</SelectItem>
                                <SelectItem value="out_of_stock">Out of Stock</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="flex gap-2 pt-4">
                          <Button onClick={handleUpdateArtwork} className="flex-1">
                            Update Artwork
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

                  {/* Restock */}
                  {artwork.status === 'out_of_stock' && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="ghost" size="sm" onClick={() => setRestockingArtwork(artwork)}>
                          <Package className="w-4 h-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-md">
                        <DialogHeader>
                          <DialogTitle>Restock Artwork</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                          <p className="text-sm text-muted-foreground">
                            Current quantity: {artwork.quantity}
                          </p>
                          <div>
                            <Label htmlFor="restock-quantity">Add Quantity</Label>
                            <Input
                              id="restock-quantity"
                              type="number"
                              min="1"
                              value={restockQuantity}
                              onChange={(e) => setRestockQuantity(parseInt(e.target.value) || 1)}
                            />
                          </div>
                          <div className="flex gap-2 pt-4">
                            <Button onClick={handleRestock} className="flex-1">
                              Restock
                            </Button>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  )}

                  {/* Delete */}
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(artwork._id)}>
                    <Trash className="w-4 h-4" />
                  </Button>
                </div>
              </TableCell>

              {/* AI Boost */}
              <TableCell>
                <Button variant="ghost" size="sm" onClick={() => handleAiBoost(artwork)}>
                  <TrendingUp className="w-4 h-4 text-green-600" />
                </Button>
                <Dialog
                  open={!!aiBoostingArtwork}
                  onOpenChange={(open) => {
                    if (!open) {
                      setAiBoostingArtwork(null);
                      setAiBoostData(null);
                      setAiBoostError(null);
                    }
                  }}
                >
                  <DialogContent
                    className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2
               w-[600px] max-w-full h-[70vh] bg-white rounded-lg shadow-lg
               overflow-y-auto p-6
               "
                    style={{ backgroundColor: 'white', zIndex: 50 }}
                  >
                    <div className="fixed inset-0 z-40"></div>
                    <DialogHeader>
                      <DialogTitle>AI Boost for: {aiBoostingArtwork?.title}</DialogTitle>
                    </DialogHeader>

                    {aiBoostingArtwork?.media?.[0]?.url && (
                      <div className="mb-4">
                        <img
                          src={aiBoostingArtwork.media[0].url}
                          alt={aiBoostingArtwork.title}
                          className="w-full max-h-64 object-contain rounded-lg shadow"
                        />
                      </div>
                    )}

                    {aiBoostData ? (
                      <div className="space-y-4">
                        {/* Purchase Analysis */}
                        {aiBoostData.purchase_analysis && (
                          <div>
                            <h4 className="font-semibold">AI Purchase Analysis:</h4>
                            <p className="text-muted-foreground">{aiBoostData.purchase_analysis}</p>
                          </div>
                        )}

                        {/* Suggested Complementary Items */}
                        {aiBoostData.cart_suggestions?.length > 0 && (
                          <div>
                            <h4 className="font-semibold">Suggested Complementary Items:</h4>
                            <ul className="list-disc list-inside">
                              {aiBoostData.cart_suggestions.map((item: string, index: number) => (
                                <li key={index}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {/* Packaging Suggestions */}
                        {aiBoostData.packaging_suggestions?.length > 0 && (
                          <div>
                            <h4 className="font-semibold">Packaging Suggestions:</h4>
                            <ul className="list-disc list-inside">
                              {aiBoostData.packaging_suggestions.map((item: string, index: number) => (
                                <li key={index}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {/* Shipping Considerations */}
                        {aiBoostData.shipping_considerations && (
                          <div>
                            <h4 className="font-semibold">Shipping Considerations:</h4>
                            <p className="text-muted-foreground">{aiBoostData.shipping_considerations}</p>
                          </div>
                        )}
                      </div>
                    ) : aiBoostError ? (
                      <div className="text-red-500 text-center py-8">
                        <p className="font-semibold">AI Boost failed</p>
                        <p className="text-sm text-muted-foreground">{aiBoostError}</p>
                      </div>
                    ) : (
                      <div className="flex justify-center py-8">
                        <Loader text="Boosting sales with AI..." />
                      </div>
                    )}
                  </DialogContent>
                </Dialog>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
};