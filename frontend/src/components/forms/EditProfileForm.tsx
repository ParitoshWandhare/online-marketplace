import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { userService } from '@/services/user';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/context/AuthContext';

const editProfileSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  phone: z.string().optional(),
  bio: z.string().optional(),
  region: z.string().optional(),
  avatarUrl: z.string().url('Invalid URL').optional().or(z.literal('')),
});

type EditProfileFormData = z.infer<typeof editProfileSchema>;

interface EditProfileFormProps {
  onSuccess?: () => void;
}

export const EditProfileForm = ({ onSuccess }: EditProfileFormProps) => {
  const { user, loadProfile } = useAuth();
  const { toast } = useToast();

  const form = useForm<EditProfileFormData>({
    resolver: zodResolver(editProfileSchema),
    defaultValues: {
      name: user?.name || '',
      phone: user?.phone || '',
      bio: user?.bio || '',
      region: user?.region || '',
      avatarUrl: user?.avatarUrl || '',
    },
  });

  const onSubmit = async (data: EditProfileFormData) => {
    try {
      const response = await userService.updateProfile({
        name: data.name,
        phone: data.phone || undefined,
        bio: data.bio || undefined,
        region: data.region || undefined,
        avatarUrl: data.avatarUrl || undefined,
      });

      if (response.success) {
        await loadProfile(); // Refresh user data
        toast({
          title: 'Success',
          description: 'Profile updated successfully!',
        });
        onSuccess?.();
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to update profile. Please try again.',
      });
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter your name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="phone"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Phone</FormLabel>
              <FormControl>
                <Input placeholder="Enter your phone number" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="avatarUrl"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Avatar URL</FormLabel>
              <FormControl>
                <Input placeholder="https://example.com/avatar.jpg" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="region"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Region</FormLabel>
              <FormControl>
                <Input placeholder="Enter your region/location" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="bio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bio</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="Tell us about yourself..."
                  className="min-h-[100px]"
                  {...field} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex gap-3 pt-4">
          <Button type="submit" className="flex-1">
            Update Profile
          </Button>
          <Button type="button" variant="outline" onClick={onSuccess}>
            Cancel
          </Button>
        </div>
      </form>
    </Form>
  );
};