import { Link } from 'react-router-dom';
import { LoginForm } from '@/components/forms/LoginForm';
import { ShoppingBag } from 'lucide-react';

const LoginPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent-purple/5">
        <div className="absolute inset-0" style={{ background: 'var(--gradient-mesh)' }} />
      </div>
      
      <div className="relative max-w-md w-full mx-4 space-y-8 animate-scale-in">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gradient-to-r from-primary to-accent-purple rounded-2xl flex items-center justify-center mb-6 animate-float">
            <ShoppingBag className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold">Welcome Back</h2>
          <p className="text-muted-foreground">
            Sign in to continue your shopping journey
          </p>
        </div>
        
        <div className="bg-card/80 backdrop-blur-sm rounded-3xl p-8 shadow-xl border card-hover">
          <LoginForm />
        </div>
        
        <div className="text-center">
          <span className="text-muted-foreground">Don't have an account? </span>
          <Link to="/signup" className="text-primary hover:underline font-medium transition-colors">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;