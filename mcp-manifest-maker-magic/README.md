
# MCP Generator

A beautiful, modern web application for generating Model Context Protocol (MCP) servers from APIs. Transform your API endpoints or OpenAPI specifications into MCP servers in seconds.

## Features

- **Dual Input Methods**: Support for both API URL endpoints and OpenAPI 3.x specifications
- **Real-time Generation**: Live progress logs during MCP server generation
- **Modern UI**: Clean, professional interface with dark theme
- **Responsive Design**: Works beautifully on desktop and mobile devices
- **TypeScript**: Fully typed for better development experience
- **Form Validation**: Comprehensive input validation with helpful error messages

## Tech Stack

- **React 18** with functional components and hooks
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React Hook Form** for form management and validation
- **Axios** for HTTP requests
- **React Hot Toast** for notifications
- **Vite** for fast development and building
- **Lucide React** for beautiful icons

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-generator
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Usage

1. **API URL Tab**: Enter your API endpoint URL to generate an MCP server
2. **OpenAPI Spec Tab**: Paste your OpenAPI 3.x specification (YAML or JSON)
3. Click "Generate MCP Server" to start the process
4. Watch real-time logs as your server is generated
5. Copy the generated manifest URL and quick-start code for Claude

## API Integration

The app expects a backend endpoint at `/api/generate-mcp` that accepts:

```typescript
// For API URL
{
  "apiUrl": "https://api.example.com"
}

// For OpenAPI Spec
{
  "openApiSpec": "your-openapi-spec-content"
}
```

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## License

MIT License
