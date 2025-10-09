import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, Star, Users, ShoppingBag, Sparkles } from 'lucide-react';
import heroImage from '@/assets/hero-marketplace.jpg';
import communityImage from '@/assets/shopping-community.jpg';

const LandingPage = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background with mesh gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-background via-primary/5 to-background">
          <div className="absolute inset-0" style={{ background: 'var(--gradient-mesh)' }} />
        </div>
        
        <div className="relative container mx-auto px-4 py-20 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-fade-in">
              <div className="space-y-4">
                <div className="inline-flex items-center rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary animate-pulse-glow">
                  <Sparkles className="w-4 h-4 mr-2" />
                  New Marketplace Experience
                </div>
                <h1 className="text-4xl lg:text-6xl font-bold leading-tight">
                  Discover Amazing
                  <span className="block bg-gradient-to-r from-primary via-accent-purple to-accent-pink bg-clip-text text-transparent">
                    Products Daily
                  </span>
                </h1>
                <p className="text-xl text-muted-foreground max-w-lg">
                  Join thousands of sellers and buyers at ORCHID. Find unique items, support local businesses, and discover your next favorite purchase.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button asChild size="lg" className="btn-gradient group animate-bounce-gentle">
                  <Link to="/signup">
                    Start Shopping
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="card-hover">
                  <Link to="/login">
                    Sign In
                  </Link>
                </Button>
              </div>
              
              <div className="flex items-center gap-8 pt-8">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">10K+</div>
                  <div className="text-sm text-muted-foreground">Happy Customers</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">5K+</div>
                  <div className="text-sm text-muted-foreground">Products</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">99%</div>
                  <div className="text-sm text-muted-foreground">Satisfaction</div>
                </div>
              </div>
            </div>
            
            <div className="relative animate-float">
              <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-accent-pink/20 rounded-3xl blur-3xl" />
              <img
                src={heroImage}
                alt="Marketplace hero"
                className="relative rounded-3xl shadow-2xl w-full h-auto"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-slide-up">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">
              Why Choose ORCHID?
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Experience the future of online shopping with our innovative features
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: ShoppingBag,
                title: "Curated Products",
                description: "Handpicked items from trusted sellers worldwide",
                gradient: "from-primary to-accent-purple"
              },
              {
                icon: Users,
                title: "Community Driven",
                description: "Connect with buyers and sellers in our vibrant community",
                gradient: "from-accent-purple to-accent-pink"
              },
              {
                icon: Star,
                title: "Premium Experience",
                description: "Enjoy seamless shopping with advanced AI recommendations",
                gradient: "from-accent-pink to-accent-orange"
              }
            ].map((feature, index) => (
              <div key={index} className="group card-hover rounded-2xl p-8 bg-card animate-scale-in" style={{ animationDelay: `${index * 0.2}s` }}>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.gradient} p-3 mb-6 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Community Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-scale-in">
              <img
                src={communityImage}
                alt="Shopping community"
                className="rounded-3xl shadow-xl w-full h-auto"
              />
            </div>
            
            <div className="space-y-6 animate-slide-up">
              <h2 className="text-3xl lg:text-4xl font-bold">
                Join Our Growing
                <span className="block text-primary">Community</span>
              </h2>
              <p className="text-lg text-muted-foreground">
                Connect with like-minded shoppers, discover new trends, and get personalized recommendations from our AI-powered system.
              </p>
              
              <div className="space-y-4">
                {[
                  "AI-powered product recommendations",
                  "Real-time inventory updates",
                  "Secure payment processing",
                  "24/7 customer support"
                ].map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                      <Star className="w-3 h-3 text-primary" />
                    </div>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              
              <Button asChild size="lg" className="btn-gradient">
                <Link to="/signup">
                  Get Started Today
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary via-accent-purple to-accent-pink opacity-10" />
        <div className="relative container mx-auto px-4 text-center">
          <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
            <h2 className="text-3xl lg:text-5xl font-bold">
              Ready to Start Your
              <span className="block text-primary">Shopping Journey?</span>
            </h2>
            <p className="text-xl text-muted-foreground">
              Join thousands of satisfied customers and discover amazing products today
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg" className="btn-gradient animate-pulse-glow">
                <Link to="/signup">
                  Create Account
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="card-hover">
                <Link to="/login">
                  Sign In
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;