import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Globe, FileCode, Loader2, CheckCircle, Copy, Package } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface FormData {
  apiUrl?: string;
  openApiSpec?: string;
}

interface GenerationResult {
  manifestUrl: string;
  downloadUrl: string;
}

const GeneratorCard = () => {
  const [activeTab, setActiveTab] = useState<'url' | 'spec'>('url');
  const [isGenerating, setIsGenerating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>();

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Copied to clipboard!');
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const onSubmit = async (data: FormData) => {
    setIsGenerating(true);
    setLogs([]);
    setError(null);
    setResult(null);

    try {
      addLog('Started MCP server generation...');
      
      // Prepare the request message for root_agent
      const requestMessage = activeTab === 'url' 
        ? `Generate an MCP server for the API at ${data.apiUrl}`
        : `Generate an MCP server from this OpenAPI specification:\n\n${data.openApiSpec}`;

      addLog('Connecting to Root Agent...');

      // Create A2A protocol request
      const a2aRequest = {
        message: {
          role: "user",
          content: requestMessage
        }
      };

      addLog('Analyzing API structure...');
      
      // Call the root_agent through the proxy
      const response = await axios.post('http://127.0.0.1:10000/tasks/send', a2aRequest, {
        timeout: 600000000, // Increased timeout for complex operations
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Poll for task completion
      const taskId = response.data.id;
      let taskResult = response.data;
      
      while (taskResult.status?.state !== 'completed' && taskResult.status?.state !== 'failed') {
        addLog('Processing request...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const statusResponse = await axios.get(`/root-agent/tasks/${taskId}`);
        taskResult = statusResponse.data;
        
        // Check for intermediate messages
        if (taskResult.status?.message?.content?.text) {
          addLog(taskResult.status.message.content.text);
        }
      }

      if (taskResult.status?.state === 'failed') {
        throw new Error(taskResult.status?.message?.content?.text || 'Task failed');
      }

      addLog('MCP server generated successfully!');
      
      // Extract the result from the artifacts
      const artifactText = taskResult.artifacts?.[0]?.parts?.[0]?.text || '';
      
      // Parse the response to extract relevant information
      // For now, we'll use placeholder URLs, but in a real implementation,
      // these would be extracted from the agent's response
      setResult({
        manifestUrl: '/root-agent/generated/manifest.json',
        downloadUrl: '/root-agent/generated/download'
      });

      // Show the full response in logs
      if (artifactText) {
        addLog('Response from Root Agent:');
        artifactText.split('\n').forEach((line: string) => {
          if (line.trim()) addLog(line);
        });
      }

    } catch (err: any) {
      const errorMessage = err.response?.data?.message || err.message || 'Generation failed';
      setError(errorMessage);
      addLog(`Error: ${errorMessage}`);
      toast.error('Generation failed. Please ensure the Root Agent is running on port 10000.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setLogs([]);
    reset();
  };

  if (result) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-card border border-border rounded-lg p-8 shadow-xl">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-primary rounded-lg flex items-center justify-center mx-auto mb-4">
              <Package className="w-8 h-8 text-primary-foreground" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">Your MCP Server</h2>
            <p className="text-muted-foreground text-sm">Generated manifest and download link will appear here after successful generation.</p>
          </div>

          <div className="space-y-4">
            <div className="bg-muted rounded-lg p-4 border border-border">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-foreground">Manifest URL</label>
                <button
                  onClick={() => copyToClipboard(result.manifestUrl)}
                  className="text-primary hover:text-primary/80 transition-colors"
                >
                  <Copy size={16} />
                </button>
              </div>
              <code className="text-sm text-muted-foreground break-all font-mono">{result.manifestUrl}</code>
            </div>

            <div className="bg-muted rounded-lg p-4 border border-border">
              <h3 className="text-sm font-medium text-foreground mb-2">Quick-start for Claude</h3>
              <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-mono">
{`// Add to your Claude configuration
{
  "mcpServers": {
    "custom-api": {
      "command": "node",
      "args": ["path/to/server.js"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}`}
              </pre>
              <button
                onClick={() => copyToClipboard(`// Add to your Claude configuration...`)}
                className="mt-2 text-primary hover:text-primary/80 transition-colors text-sm"
              >
                Copy configuration
              </button>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="w-full mt-6 bg-secondary hover:bg-secondary/80 text-secondary-foreground py-3 px-4 rounded-lg transition-colors"
          >
            Generate Another Server
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-card border border-border rounded-lg overflow-hidden shadow-xl">
        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('url')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors flex items-center justify-center space-x-2 ${
              activeTab === 'url'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
            }`}
          >
            <Globe size={18} />
            <span>API URL</span>
          </button>
          <button
            onClick={() => setActiveTab('spec')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors flex items-center justify-center space-x-2 ${
              activeTab === 'spec'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
            }`}
          >
            <FileCode size={18} />
            <span>OpenAPI Spec</span>
          </button>
        </div>

        {/* Form Content */}
        <div className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {activeTab === 'url' ? (
              <div>
                <label htmlFor="apiUrl" className="block text-sm font-medium text-foreground mb-2">
                  API Endpoint URL
                </label>
                <input
                  {...register('apiUrl', {
                    required: 'API URL is required',
                    pattern: {
                      value: /^https?:\/\/.+/,
                      message: 'Please enter a valid URL'
                    }
                  })}
                  type="url"
                  id="apiUrl"
                  placeholder="https://api.example.com"
                  className="w-full px-4 py-3 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all"
                />
                {errors.apiUrl && (
                  <p className="mt-2 text-sm text-destructive">{errors.apiUrl.message}</p>
                )}
                <p className="mt-2 text-sm text-muted-foreground">
                  Enter the URL of your API endpoint
                </p>
              </div>
            ) : (
              <div>
                <label htmlFor="openApiSpec" className="block text-sm font-medium text-foreground mb-2">
                  OpenAPI Specification
                </label>
                <textarea
                  {...register('openApiSpec', {
                    required: 'OpenAPI specification is required'
                  })}
                  id="openApiSpec"
                  rows={8}
                  placeholder="Paste your OpenAPI 3.x specification (YAML or JSON)..."
                  className="w-full px-4 py-3 bg-input border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all font-mono text-sm"
                />
                {errors.openApiSpec && (
                  <p className="mt-2 text-sm text-destructive">{errors.openApiSpec.message}</p>
                )}
                <p className="mt-2 text-sm text-muted-foreground">
                  Supports both YAML and JSON formats
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={isGenerating}
              className="w-full bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-primary-foreground py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Generating MCP Server...</span>
                </>
              ) : (
                <>
                  <FileCode size={18} />
                  <span>Generate MCP Server</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Live Logs */}
        {logs.length > 0 && (
          <div className="border-t border-slate-600 bg-slate-900">
            <div className="p-4">
              <h3 className="text-sm font-medium text-slate-300 mb-3 flex items-center space-x-2">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span>Generation Progress</span>
              </h3>
              <pre className="text-sm text-slate-400 bg-slate-800 rounded-lg p-3 max-h-40 overflow-y-auto font-mono">
                {logs.join('\n')}
              </pre>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="border-t border-slate-600 bg-red-900 p-4">
            <div className="flex items-center space-x-2 text-red-400">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GeneratorCard;
