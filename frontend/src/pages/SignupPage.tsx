import { useState } from 'react';
import { Link } from 'react-router-dom';
import { SignupForm } from '@/components/forms/SignupForm';
import { Users } from 'lucide-react';

const SignupPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent-purple/5 via-background to-accent-pink/5">
        <div className="absolute inset-0" style={{ background: 'var(--gradient-mesh)' }} />
      </div>
      
      <div className="relative max-w-md w-full mx-4 space-y-8 animate-slide-up">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gradient-to-r from-accent-purple to-accent-pink rounded-2xl flex items-center justify-center mb-6 animate-bounce-gentle">
            <Users className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold">Create Your Account</h2>
          <p className="text-muted-foreground">
            Join our marketplace community today
          </p>
        </div>
        
        <div className="bg-card/80 backdrop-blur-sm rounded-3xl p-8 shadow-xl border card-hover">
          <SignupForm />
        </div>
        
        <div className="text-center">
          <span className="text-muted-foreground">Already have an account? </span>
          <Link to="/login" className="text-primary hover:underline font-medium transition-colors">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;