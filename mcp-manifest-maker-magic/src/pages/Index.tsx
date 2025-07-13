
import { Toaster } from 'react-hot-toast';
import Header from '../components/Header';
import GeneratorCard from '../components/GeneratorCard';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Hero Section */}
      <div className="pt-20 pb-12 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-2xl md:text-3xl font-bold text-foreground mb-3 tracking-tight">
            Generate MCP Servers
          </h1>
          <p className="text-sm text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
            Transform your API into a Model Context Protocol server in seconds. 
            Simply provide your API endpoint or OpenAPI specification.
          </p>
        </div>
      </div>

      {/* Main Generator Card */}
      <div className="px-4 pb-20">
        <GeneratorCard />
      </div>

      {/* Toast Notifications */}
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'hsl(var(--card))',
            color: 'hsl(var(--card-foreground))',
            border: '1px solid hsl(var(--border))'
          }
        }}
      />
    </div>
  );
};

export default Index;
