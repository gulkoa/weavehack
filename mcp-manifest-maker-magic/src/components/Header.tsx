
import { Github, FileText, Home, Book } from 'lucide-react';

const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary rounded-sm flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">M</span>
            </div>
            <span className="text-foreground text-xl font-semibold">MCP Generator</span>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2 text-sm">
              <Home size={18} />
              <span>Home</span>
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2 text-sm">
              <Book size={18} />
              <span>Documentation</span>
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2 text-sm">
              <FileText size={18} />
              <span>About</span>
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2 text-sm">
              <Github size={18} />
              <span>GitHub</span>
            </a>
          </nav>

          {/* Mobile menu button */}
          <button className="md:hidden text-muted-foreground hover:text-foreground">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
