#!/usr/bin/env python3
"""
Dynamic Modular MCP Server

A single MCP server that can dynamically load and expose functions from multiple Python modules.
New functionality can be added by simply dropping Python files into the plugins directory.
"""

import os
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Any, Callable
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

# Our existing function analyzer
from convert_to_mcp import FunctionAnalyzer

class ModularMCPServer:
    """Dynamic MCP server that loads functions from plugin modules."""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.functions = {}  # function_name -> (module, function, metadata)
        self.tools_metadata = []
        
        # Initialize FastAPI
        self.app = FastAPI(
            title="Modular MCP Server",
            description="Dynamic MCP server with plugin-based functionality",
            version="1.0.0"
        )
        
        # Add CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Load plugins and setup routes
        self.load_plugins()
        self.setup_routes()
    
    def load_plugins(self):
        """Dynamically load all Python files from plugins directory."""
        print(f"🔍 Scanning for plugins in {self.plugins_dir}...")
        
        if not self.plugins_dir.exists():
            print(f"⚠️  Plugins directory {self.plugins_dir} not found, creating...")
            self.plugins_dir.mkdir(exist_ok=True)
            return
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private files
                
            try:
                self.load_plugin(plugin_file)
            except Exception as e:
                print(f"❌ Failed to load plugin {plugin_file}: {e}")
    
    def load_plugin(self, plugin_file: Path):
        """Load a single plugin file and extract its functions."""
        print(f"📦 Loading plugin: {plugin_file.name}")
        
        # Use our existing function analyzer
        try:
            analyzer = FunctionAnalyzer(str(plugin_file))
            functions_metadata = analyzer.extract_functions()
            
            if not functions_metadata:
                print(f"   ⚠️  No suitable functions found in {plugin_file.name}")
                return
            
            # Import the module dynamically
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Register each function
            for func_meta in functions_metadata:
                func_name = func_meta['name']
                func_obj = getattr(module, func_name)
                
                self.functions[func_name] = {
                    'module': module,
                    'function': func_obj,
                    'metadata': func_meta,
                    'plugin_file': plugin_file.name
                }
                
                self.tools_metadata.append({
                    "name": func_name,
                    "description": func_meta['description'],
                    "inputSchema": func_meta['input_schema']
                })
                
                print(f"   ✅ Registered function: {func_name}")
                
        except Exception as e:
            print(f"   ❌ Error loading {plugin_file}: {e}")
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def get_manifest():
            """Serve the dynamic MCP manifest."""
            manifest = {
                "schema_version": "1.0",
                "name": "modular-mcp",
                "description": f"Dynamic MCP server with {len(self.functions)} loaded functions",
                "version": "1.0.0",
                "tools": self.tools_metadata
            }
            return JSONResponse(content=manifest)
        
        @self.app.get("/plugins")
        async def list_plugins():
            """List all loaded plugins and their functions."""
            plugins_info = {}
            for func_name, func_info in self.functions.items():
                plugin_name = func_info['plugin_file']
                if plugin_name not in plugins_info:
                    plugins_info[plugin_name] = []
                plugins_info[plugin_name].append({
                    'name': func_name,
                    'description': func_info['metadata']['description']
                })
            return JSONResponse(content=plugins_info)
        
        @self.app.post("/call/{function_name}")
        async def call_function(function_name: str, request_data: dict):
            """Dynamically call any loaded function."""
            if function_name not in self.functions:
                raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")
            
            func_info = self.functions[function_name]
            func_obj = func_info['function']
            
            try:
                # Call the function with the provided arguments
                result = func_obj(**request_data)
                return JSONResponse(content={"result": result})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error calling {function_name}: {str(e)}")
        
        @self.app.get("/health")
        async def health_check():
            """Health check with plugin status."""
            return {
                "status": "healthy",
                "plugins_loaded": len(set(info['plugin_file'] for info in self.functions.values())),
                "functions_available": len(self.functions)
            }
        
        # Generate specific endpoints for each function (for backward compatibility)
        self.create_function_endpoints()
    
    def create_function_endpoints(self):
        """Create specific endpoints for each function."""
        for func_name, func_info in self.functions.items():
            metadata = func_info['metadata']
            func_obj = func_info['function']
            
            # Create a closure to capture the function
            def make_endpoint(func_obj):
                async def function_endpoint(request_data: dict):
                    try:
                        result = func_obj(**request_data)
                        return JSONResponse(content={"result": result})
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
                return function_endpoint
            
            # Add the route
            endpoint = make_endpoint(func_obj)
            self.app.add_api_route(f"/{func_name}", endpoint, methods=["POST"])
            print(f"   🔗 Created endpoint: /{func_name}")
    
    def reload_plugins(self):
        """Hot-reload all plugins (useful for development)."""
        print("🔄 Reloading plugins...")
        self.functions.clear()
        self.tools_metadata.clear()
        self.load_plugins()
        print(f"✅ Reloaded {len(self.functions)} functions")

# Global server instance
server = None

def create_server():
    """Create the modular MCP server."""
    global server
    if server is None:
        server = ModularMCPServer()
    return server.app

def main():
    """Run the server."""
    import uvicorn
    app = create_server()
    
    print(f"\n🚀 Starting Modular MCP Server...")
    print(f"📁 Plugins directory: plugins/")
    print(f"🔧 Functions loaded: {len(server.functions)}")
    print(f"🌐 Server URL: http://localhost:8080")
    print(f"📋 Manifest: http://localhost:8080/")
    print(f"🔌 Plugins info: http://localhost:8080/plugins")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
