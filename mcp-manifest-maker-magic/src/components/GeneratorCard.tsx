import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  MessageSquare,
  Loader2,
  CheckCircle,
  Copy,
  Package,
} from "lucide-react";
import axios from "axios";
import toast from "react-hot-toast";

interface FormData {
  query: string;
}

interface GenerationResult {
  manifestUrl: string;
  downloadUrl: string;
}

const GeneratorCard = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>();

  const addLog = (message: string) => {
    setLogs((prev) => [
      ...prev,
      `${new Date().toLocaleTimeString()}: ${message}`,
    ]);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard!");
    } catch (err) {
      toast.error("Failed to copy to clipboard");
    }
  };

  const onSubmit = async (data: FormData) => {
    setIsGenerating(true);
    setLogs([]);
    setError(null);
    setResult(null);

    try {
      addLog("Started MCP server generation...");

      // Use the natural language query directly
      const inputText = data.query;

      addLog("Connecting to MCP generation agent...");

      // A2A Agent Communication
      const a2aPayload = {
        message: {
          role: "user",
          content: inputText,
        },
      };

      addLog("Sending request to MCP generation agent...");

      // Send to the root agent that orchestrates the full process
      const response = await axios.post(
        "http://127.0.0.1:10000/tasks/send",
        a2aPayload,
        {
          timeout: 600000000, // Increased timeout for complex operations
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      addLog("Received response from MCP generation agent...");

      const respData = response.data;
      console.log({ respData });

      if (respData?.artifacts?.[0]?.parts?.[0]?.text) {
        const mcpServerCode = respData.artifacts[0].parts[0].text;
        addLog("MCP server generated successfully!");

        // Set result with the MCP server code
        setResult({
          manifestUrl: `MCP Server for query: "${data.query}"`,
          downloadUrl: mcpServerCode,
        });
      } else {
        throw new Error("No MCP server code found in agent response");
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.error?.message ||
        err.message ||
        "MCP server generation failed";
      setError(errorMessage);
      addLog(`Error: ${errorMessage}`);
      toast.error("MCP server generation failed. Please try again.");
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
        <div className="bg-card border border-border rounded-none p-8 shadow-xl">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-primary rounded-none flex items-center justify-center mx-auto mb-4">
              <Package className="w-8 h-8 text-primary-foreground" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">
              MCP Server Ready
            </h2>
            <p className="text-muted-foreground text-sm">
              Your complete MCP server Python file has been generated.
            </p>
          </div>

          <div className="space-y-4">
            <div className="bg-muted rounded-none p-4 border border-border">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-foreground">
                  Your Request
                </label>
                <button
                  onClick={() => copyToClipboard(result.manifestUrl)}
                  className="text-primary hover:text-primary/80 transition-colors"
                >
                  <Copy size={16} />
                </button>
              </div>
              <code className="text-sm text-muted-foreground break-all font-mono">
                {result.manifestUrl}
              </code>
            </div>

            <div className="bg-muted rounded-none p-4 border border-border max-h-96 overflow-y-auto">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-foreground">
                  Response
                </label>
                <button
                  onClick={() => copyToClipboard(result.downloadUrl)}
                  className="text-primary hover:text-primary/80 transition-colors"
                >
                  <Copy size={16} />
                </button>
              </div>
              <div className="text-sm text-muted-foreground whitespace-pre-wrap font-mono">
                {result.downloadUrl}
              </div>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="w-full mt-6 bg-secondary hover:bg-secondary/80 text-secondary-foreground py-3 px-4 rounded-none transition-colors"
          >
            Generate Another MCP Server
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-card border border-cyan-400 rounded-none overflow-hidden">
        {/* Form Content */}
        <div className="p-6">
          <div className="mb-6 text-center">
            <MessageSquare className="w-12 h-12 text-primary mx-auto mb-3" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              MCP Server Generator
            </h2>
            <p className="text-sm text-muted-foreground">
              Describe what API integration you need and get a complete MCP
              server Python file
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label
                htmlFor="query"
                className="block text-sm font-medium text-foreground mb-2"
              >
                What MCP server would you like to create?
              </label>
              <textarea
                {...register("query", {
                  required: "Please describe what MCP server you need",
                  minLength: {
                    value: 10,
                    message:
                      "Please provide more details (at least 10 characters)",
                  },
                })}
                id="query"
                rows={4}
                placeholder="Examples:
• Create an MCP server for the GitHub API to manage repositories
• Generate MCP tools for Stripe payment processing
• Build MCP server for Twitter API integration
• I need MCP tools for OpenAI's text generation API"
                className="w-full px-4 py-3 bg-input border border-cyan-400/40 focus:border-cyan-400 rounded-none text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan-400/60 focus:shadow-lg focus:shadow-cyan-400/20 transition-all text-sm"
              />
              {errors.query && (
                <p className="mt-2 text-sm text-destructive">
                  {errors.query.message}
                </p>
              )}
              <p className="mt-2 text-sm text-muted-foreground">
                Describe the API you want to integrate and what functionality
                you need
              </p>
            </div>

            <button
              type="submit"
              disabled={isGenerating}
              className="w-full bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-primary-foreground py-3 px-6 rounded-none font-medium transition-colors flex items-center justify-center space-x-2 border border-cyan-400 hover:border-cyan-300 hover:shadow-lg hover:shadow-cyan-400/40"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Generating MCP Server...</span>
                </>
              ) : (
                <>
                  <MessageSquare size={18} />
                  <span>Generate MCP Server</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Live Logs */}
        {logs.length > 0 && (
          <div className="border-t border-cyan-400/30 bg-slate-900">
            <div className="p-4">
              <h3 className="text-sm font-medium text-slate-300 mb-3 flex items-center space-x-2">
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-lg shadow-cyan-400/60"></div>
                <span>Generation Progress</span>
              </h3>
              <pre className="text-sm text-slate-400 bg-slate-800 rounded-none p-3 max-h-40 overflow-y-auto font-mono">
                {logs.join("\n")}
              </pre>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="border-t border-cyan-400/30 bg-red-900 p-4">
            <div className="flex items-center space-x-2 text-red-400">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
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
