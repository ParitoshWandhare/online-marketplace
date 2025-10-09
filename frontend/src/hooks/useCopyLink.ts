import { useCallback } from 'react';
import { copyToClipboard } from '@/lib/clipboard';
import { useToast } from '@/hooks/use-toast';

export const useCopyLink = () => {
  const { toast } = useToast();

  const copyLink = useCallback(async (url: string, itemTitle?: string) => {
    const success = await copyToClipboard(url);
    
    if (success) {
      toast({
        title: 'Link copied!',
        description: itemTitle 
          ? `Link to "${itemTitle}" copied to clipboard`
          : 'Link copied to clipboard',
      });
    } else {
      toast({
        title: 'Failed to copy',
        description: 'Please try again or copy manually',
        variant: 'destructive',
      });
    }
    
    return success;
  }, [toast]);

  return { copyLink };
};