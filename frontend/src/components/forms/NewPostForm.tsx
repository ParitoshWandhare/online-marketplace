import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Sparkles, Upload, X } from 'lucide-react';
import { useState } from 'react';
import { visionAiService } from "@/services/visionAi";
import { artworkService } from '@/services/artwork';
import { useToast } from '@/hooks/use-toast';

const newPostSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  price: z.number().min(0.01, 'Price must be greater than 0'),
  currency: z.string().min(1, 'Currency is required'),
  quantity: z.number().min(1, 'Quantity must be at least 1'),
  status: z.enum(['draft', 'published']),
  media: z.any().optional(),
});

type NewPostFormData = z.infer<typeof newPostSchema>;

export const NewPostForm = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [previewFiles, setPreviewFiles] = useState<Array<{ file: File; url: string }>>([]);
  const [aiSuggestion, setAiSuggestion] = useState<{
    price_range: string;
    market_analysis: string;
    reasoning: string;
  } | null>(null);
  const { toast } = useToast();

  const form = useForm<NewPostFormData>({
    resolver: zodResolver(newPostSchema),
    defaultValues: {
      title: '',
      description: '',
      price: 0,
      currency: 'INR',
      quantity: 1,
      status: 'draft' as const,
    },
  });

  // AI Price Suggestion
  const generatePriceSuggestion = async () => {
    setIsGenerating(true);
    try {
      const title = form.getValues('title');
      const description = form.getValues('description');

      const resp = await visionAiService.priceSuggestion(previewFiles[0]?.file);

      if (resp.data) {
        setAiSuggestion(resp.data);

        if (resp.data.price_range) {
          const [min, max] = resp.data.price_range
            .replace(/[₹$,]/g, '')
            .split('-')
            .map((val) => parseFloat(val.trim()));
          if (!isNaN(min) && !isNaN(max)) {
            const avgPrice = (min + max) / 2;
            form.setValue('price', avgPrice);
          }
        }
      } else {
        toast({
          variant: 'destructive',
          title: 'AI Error',
          description: resp.error || 'Could not generate price suggestion',
        });
      }

    } catch (error) {
      console.error('Failed to generate price suggestion:', error);
      toast({
        variant: 'destructive',
        title: 'AI Error',
        description: 'Could not generate price suggestion',
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const limitedFiles = files.slice(0, 5 - previewFiles.length);
    const newPreviews = limitedFiles.map((file) => ({
      file,
      url: URL.createObjectURL(file),
    }));
    const allPreviews = [...previewFiles, ...newPreviews];
    setPreviewFiles(allPreviews);

    const fileList = new DataTransfer();
    allPreviews.forEach((preview) => fileList.items.add(preview.file));
    form.setValue('media', fileList.files.length > 0 ? fileList.files : undefined);

    e.target.value = '';
  };

  const removeFile = (indexToRemove: number) => {
    const updatedPreviews = previewFiles.filter((_, index) => index !== indexToRemove);
    URL.revokeObjectURL(previewFiles[indexToRemove].url);
    setPreviewFiles(updatedPreviews);

    const fileList = new DataTransfer();
    updatedPreviews.forEach((preview) => fileList.items.add(preview.file));
    form.setValue('media', fileList.files.length > 0 ? fileList.files : undefined);
  };

  const onSubmit = async (data: NewPostFormData) => {
    setIsSubmitting(true);
    try {
      const mediaFiles = data.media as FileList | undefined;

      await artworkService.createArtwork({
        title: data.title,
        description: data.description,
        price: data.price,
        currency: data.currency,
        quantity: data.quantity,
        status: data.status,
        media: mediaFiles,
      });

      toast({
        title: 'Success',
        description: 'Product created successfully!',
      });

      previewFiles.forEach((preview) => URL.revokeObjectURL(preview.url));
      setPreviewFiles([]);
      setAiSuggestion(null);
      form.reset();
    } catch (error) {
      console.error('Error creating artwork:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to create product. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Product Title</FormLabel>
              <FormControl>
                <Input placeholder="Enter product title" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea placeholder="Describe your product" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-3 gap-4">
          <FormField
            control={form.control}
            name="price"
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center justify-between">
                  <FormLabel>Price</FormLabel>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={generatePriceSuggestion}
                    disabled={isGenerating || !form.getValues('title')}
                    className="flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    {isGenerating ? 'Analyzing...' : 'AI Price Suggest'}
                  </Button>
                </div>
                <span style={{ fontSize: '0.80rem', color: '#6B7280', display: 'block', marginTop: '0.25rem' }}>
                  Add image first to get AI price suggestion
                </span>
                <FormControl>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    {...field}
                    onChange={(e) =>
                      field.onChange(parseFloat(e.target.value) || 0)
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="currency"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Currency</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select currency" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="INR">₹ INR</SelectItem>
                    <SelectItem value="USD">$ USD</SelectItem>
                    <SelectItem value="EUR">€ EUR</SelectItem>
                    <SelectItem value="GBP">£ GBP</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="quantity"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Quantity</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="1"
                    {...field}
                    onChange={(e) =>
                      field.onChange(parseInt(e.target.value) || 1)
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {aiSuggestion && (
          <div className="p-4 border rounded-lg bg-muted/30 space-y-2">
            <p className="text-sm">
              <strong>Suggested Range:</strong> {aiSuggestion.price_range}
            </p>
            <p className="text-sm">
              <strong>Reasoning:</strong> {aiSuggestion.reasoning}
            </p>
            <p className="text-xs text-muted-foreground">
              {aiSuggestion.market_analysis}
            </p>
          </div>
        )}

        {/* ...status, media upload, previews, submit button (unchanged)... */}

        <FormField
          control={form.control}
          name="status"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Status</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="draft">Draft (Can be edited)</SelectItem>
                  <SelectItem value="published">Published (Visible to all)</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="media"
          render={() => (
            <FormItem>
              <FormLabel>Product Images</FormLabel>
              <FormControl>
                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center">
                  <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                  <Input
                    type="file"
                    multiple
                    accept="image/*,video/*"
                    onChange={handleFileChange}
                    className="hidden"
                    id="media-upload"
                  />
                  <label htmlFor="media-upload" className="cursor-pointer">
                    <p className="text-sm text-muted-foreground mb-1">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-muted-foreground">
                      PNG, JPG, GIF up to 10MB ({previewFiles.length}/5 files)
                    </p>
                  </label>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {previewFiles.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-foreground">
              Preview ({previewFiles.length}/5)
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {previewFiles.map((preview, index) => (
                <div key={index} className="relative group">
                  <img
                    src={preview.url}
                    alt={`Preview ${index + 1}`}
                    className="w-full h-24 object-cover rounded-lg border border-border"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="absolute -top-2 -right-2 w-6 h-6 rounded-full p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                  <div className="absolute bottom-1 left-1 bg-black/70 text-white text-xs px-1 rounded">
                    {Math.round(preview.file.size / 1024)}KB
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <Button type="submit" className="w-full btn-gradient" disabled={isSubmitting}>
          {isSubmitting ? 'Creating Product...' : 'Create Product'}
        </Button>
      </form>
    </Form>
  );
};
