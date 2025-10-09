import { Card, CardContent } from '@/components/ui/card';
import { Users, Target, Award, Heart } from 'lucide-react';

export const AboutPage = () => {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            About Our <span className="text-gradient">ORCHID</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            We're building a vibrant community where creative minds connect, 
            showcase their work, and turn their passion into prosperity.
          </p>
        </div>

        {/* Mission Section */}
        <div className="grid md:grid-cols-2 gap-12 items-center mb-16">
          <div>
            <h2 className="text-3xl font-bold mb-4">Our Mission</h2>
            <p className="text-muted-foreground mb-6 leading-relaxed">
              To democratize creativity by providing artists and creators with a platform 
              to showcase their unique work, connect with like-minded individuals, and 
              build sustainable creative businesses.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              We believe that everyone has something special to offer, and ORCHID 
              exists to help creators share their talents with the world while building 
              meaningful connections with their audience.
            </p>
          </div>
          <div className="relative">
            <img 
              src="/src/assets/shopping-community.jpg" 
              alt="Creative community" 
              className="rounded-lg shadow-lg"
            />
          </div>
        </div>

        {/* Values Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">Our Values</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="text-center p-6">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Users className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">Community First</h3>
                <p className="text-sm text-muted-foreground">
                  Building connections and fostering collaboration among creators
                </p>
              </CardContent>
            </Card>

            <Card className="text-center p-6">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Target className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">Quality Focus</h3>
                <p className="text-sm text-muted-foreground">
                  Maintaining high standards for all products and experiences
                </p>
              </CardContent>
            </Card>

            <Card className="text-center p-6">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Award className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">Innovation</h3>
                <p className="text-sm text-muted-foreground">
                  Continuously improving and embracing new creative possibilities
                </p>
              </CardContent>
            </Card>

            <Card className="text-center p-6">
              <CardContent className="pt-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Heart className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">Creator Support</h3>
                <p className="text-sm text-muted-foreground">
                  Empowering creators with tools and resources to succeed
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Story Section */}
        <div className="bg-muted/50 rounded-lg p-8 mb-16">
          <h2 className="text-3xl font-bold mb-6">Our Story</h2>
          <p className="text-muted-foreground mb-4 leading-relaxed">
            Founded in 2024, ORCHID started with a simple idea: creative people 
            needed a better way to share and monetize their work. What began as a small 
            platform has grown into a thriving ecosystem of thousands of creators.
          </p>
          <p className="text-muted-foreground mb-4 leading-relaxed">
            We've watched artists turn their hobbies into full-time careers, seen 
            collectors discover their next favorite piece, and witnessed countless 
            connections form between people who share a passion for creativity.
          </p>
          <p className="text-muted-foreground leading-relaxed">
            Today, we continue to innovate and expand, always keeping our core mission 
            in mind: to serve the creative community and help artistic dreams become reality.
          </p>
        </div>

        {/* Stats Section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-3xl font-bold text-primary mb-2">10K+</div>
            <div className="text-sm text-muted-foreground">Active Creators</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-primary mb-2">50K+</div>
            <div className="text-sm text-muted-foreground">Products Listed</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-primary mb-2">100K+</div>
            <div className="text-sm text-muted-foreground">Happy Customers</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-primary mb-2">25+</div>
            <div className="text-sm text-muted-foreground">Countries</div>
          </div>
        </div>
      </div>
    </div>
  );
};