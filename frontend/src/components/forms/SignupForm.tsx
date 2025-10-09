import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { SignupPayload } from '@/services/auth';

const signupSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  phone: z.string().min(10, 'Please enter a valid phone number'),
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string().min(8, 'Please confirm your password'),
  bio: z.string().max(280, 'Bio must be less than 280 characters').optional(),
  avatarUrl: z.string().url('Please enter a valid URL').optional().or(z.literal('')),
  otp: z.string().length(6, 'OTP must be 6 digits'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type SignupFormData = z.infer<typeof signupSchema>;

export const SignupForm = () => {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const { signup, sendOtp, loading } = useAuth();
  const navigate = useNavigate();

  const form = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: '', phone: '', email: '', password: '', confirmPassword: '', bio: '', avatarUrl: '', otp: ''
    },
  });

  const handleSendOtp = async () => {
    const emailValue = form.getValues('email');
    if (!emailValue) return;
    
    try {
      await sendOtp(emailValue);
      setEmail(emailValue);
      setStep(2);
    } catch (error) {
      // Error handled by AuthContext
    }
  };

  const onSubmit = async (data: SignupFormData) => {
    try {
      await signup(data as SignupPayload);
      navigate('/login');
    } catch (error) {
      // Error handled by AuthContext
    }
  };

  if (step === 1) {
    return (
      <Form {...form}>
        <div className="space-y-6">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="Enter your email" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="button" onClick={handleSendOtp} className="w-full btn-gradient hover:scale-105 transition-transform" disabled={loading}>
            {loading ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin mr-2" />
                Sending...
              </div>
            ) : (
              'Send OTP'
            )}
          </Button>
          <p style={{ fontSize: '0.85rem', color: '#6B7280', display: 'block', marginTop: '0.25rem' }}>
            Check your spam folder for OTP
          </p> 
        </div>
      </Form>
    );
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="otp"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Verification Code</FormLabel>
              <FormControl>
                <Input placeholder="Enter 6-digit code" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Full Name</FormLabel>
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
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" placeholder="Create a password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="confirmPassword"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm Password</FormLabel>
              <FormControl>
                <Input type="password" placeholder="Confirm your password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full btn-gradient hover:scale-105 transition-transform" disabled={loading}>
          {loading ? (
            <div className="flex items-center">
              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin mr-2" />
              Creating Account...
            </div>
          ) : (
            'Create Account'
          )}
        </Button>
      </form>
    </Form>
  );
};