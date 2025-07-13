#!/usr/bin/env python3
"""
Python Functions to MCP Server Converter

This script takes a Python file with documented functions and automatically
generates both a stdio-based MCP server and an HTTP-based MCP server.

Usage:
    python convert_to_mcp.py input_functions.py [--output-dir mcp_server/]
"""

import ast
import inspect
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import argparse
from pathlib import Path


class FunctionAnalyzer:
    """Analyzes Python functions to extract MCP-compatible metadata."""
    
    def __init__(self, source_file: str):
        self.source_file = source_file
        with open(source_file, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
        self.tree = ast.parse(self.source_code)
        
    def extract_functions(self) -> List[Dict[str, Any]]:
        """Extract all public functions with their metadata."""
        functions = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                func_info = self._analyze_function(node)
                if func_info:
                    functions.append(func_info)
        
        return functions
    
    def _analyze_function(self, node: ast.FunctionDef) -> Optional[Dict[str, Any]]:
        """Analyze a single function and extract MCP metadata."""
        try:
            # Get docstring
            docstring = ast.get_docstring(node)
            if not docstring:
                print(f"Warning: Function {node.name} has no docstring, skipping")
                return None
            
            # Parse arguments
            args_info = self._parse_arguments(node.args)
            
            # Parse docstring for description and parameter info
            description, param_docs, return_doc = self._parse_docstring(docstring)
            
            # Create input schema
            input_schema = self._create_input_schema(args_info, param_docs)
            
            return {
                'name': node.name,
                'description': description,
                'input_schema': input_schema,
                'return_description': return_doc,
                'docstring': docstring,
                'line_number': node.lineno
            }
            
        except Exception as e:
            print(f"Error analyzing function {node.name}: {e}")
            return None
    
    def _parse_arguments(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Parse function arguments and their types."""
        arg_info = []
        
        # Handle regular arguments
        for i, arg in enumerate(args.args):
            arg_type = "string"  # default
            required = True
            default_value = None
            
            # Check for type annotation
            if arg.annotation:
                arg_type = self._ast_to_json_type(arg.annotation)
            
            # Check for default values
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                default_value = self._ast_to_value(args.defaults[default_idx])
                required = False
            
            arg_info.append({
                'name': arg.arg,
                'type': arg_type,
                'required': required,
                'default': default_value
            })
        
        return arg_info
    
    def _parse_docstring(self, docstring: str) -> Tuple[str, Dict[str, str], str]:
        """Parse Google/Sphinx style docstring."""
        lines = docstring.strip().split('\n')
        
        # Extract main description (first paragraph)
        description_lines = []
        i = 0
        while i < len(lines) and lines[i].strip():
            description_lines.append(lines[i].strip())
            i += 1
        description = ' '.join(description_lines)
        
        # Extract parameter documentation
        param_docs = {}
        return_doc = ""
        
        current_section = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('Args:') or line.startswith('Arguments:'):
                current_section = 'args'
                continue
            elif line.startswith('Returns:'):
                current_section = 'returns'
                continue
            elif line.startswith('Example:') or line.startswith('Note:'):
                current_section = None
                continue
            
            if current_section == 'args' and ':' in line:
                # Parse parameter line: "param_name (type): description"
                match = re.match(r'\s*(\w+)\s*\([^)]+\):\s*(.+)', line)
                if match:
                    param_name, param_desc = match.groups()
                    param_docs[param_name] = param_desc
            elif current_section == 'returns' and line:
                return_doc = line
        
        return description, param_docs, return_doc
    
    def _create_input_schema(self, args_info: List[Dict], param_docs: Dict[str, str]) -> Dict[str, Any]:
        """Create JSON schema for function inputs."""
        properties = {}
        required = []
        
        for arg in args_info:
            properties[arg['name']] = {
                'type': arg['type'],
                'description': param_docs.get(arg['name'], f"Parameter {arg['name']}")
            }
            
            if arg['default'] is not None:
                properties[arg['name']]['default'] = arg['default']
            
            if arg['required']:
                required.append(arg['name'])
        
        schema = {
            'type': 'object',
            'properties': properties
        }
        
        if required:
            schema['required'] = required
        
        return schema
    
    def _ast_to_json_type(self, annotation) -> str:
        """Convert Python type annotation to JSON schema type."""
        if isinstance(annotation, ast.Name):
            type_name = annotation.id
            type_map = {
                'str': 'string',
                'int': 'integer', 
                'float': 'number',
                'bool': 'boolean',
                'list': 'array',
                'dict': 'object'
            }
            return type_map.get(type_name, 'string')
        elif isinstance(annotation, ast.Constant):
            return 'string'
        else:
            return 'string'
    
    def _ast_to_value(self, node) -> Any:
        """Convert AST node to Python value."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.List):
            return [self._ast_to_value(item) for item in node.elts]
        else:
            return None


class MCPServerGenerator:
    """Generates MCP server code from function metadata."""
    
    def __init__(self, source_file: str, functions: List[Dict[str, Any]]):
        self.source_file = source_file
        self.functions = functions
        self.module_name = Path(source_file).stem
    
    def generate_stdio_server(self) -> str:
        """Generate stdio-based MCP server code."""
        imports = f'''#!/usr/bin/env python3
"""
Auto-generated MCP Server from {self.source_file}

This server exposes the functions from {self.module_name} as MCP tools.
"""

import asyncio
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

# Import the original functions
from {self.module_name} import {", ".join(func['name'] for func in self.functions)}

# Initialize the MCP server
server = Server("{self.module_name}-mcp")
'''

        tools_list = self._generate_tools_list()
        tool_handler = self._generate_tool_handler()
        main_function = '''
async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
'''

        return imports + tools_list + tool_handler + main_function
    
    def generate_http_server(self) -> str:
        """Generate HTTP-based MCP server code."""
        imports = f'''#!/usr/bin/env python3
"""
Auto-generated HTTP MCP Server from {self.source_file}

This FastAPI server exposes the functions from {self.module_name} as HTTP endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel
import json

# Import the original functions
from {self.module_name} import {", ".join(func['name'] for func in self.functions)}

# Initialize FastAPI app
app = FastAPI(
    title="{self.module_name.title()} MCP Server",
    description="Auto-generated MCP server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''

        # Generate Pydantic models
        models = self._generate_pydantic_models()
        
        # Generate manifest endpoint
        manifest = self._generate_manifest_endpoint()
        
        # Generate tool endpoints
        endpoints = self._generate_http_endpoints()
        
        main_run = '''
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": f"{app.title}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''

        return imports + models + manifest + endpoints + main_run
    
    def _generate_tools_list(self) -> str:
        """Generate the list_tools function."""
        tools = []
        for func in self.functions:
            tool_def = f'''        Tool(
            name="{func['name']}",
            description="{func['description']}",
            inputSchema={json.dumps(func['input_schema'], indent=12)}
        )'''
            tools.append(tool_def)
        
        tools_joined = ",\n".join(tools)
        
        return f'''
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
{tools_joined}
    ]
'''
    
    def _generate_tool_handler(self) -> str:
        """Generate the call_tool function."""
        tool_cases = []
        
        for func in self.functions:
            # Generate parameter extraction
            param_extractions = []
            for prop_name, prop_info in func['input_schema']['properties'].items():
                if prop_name in func['input_schema'].get('required', []):
                    param_extractions.append(f'        {prop_name} = arguments["{prop_name}"]')
                else:
                    default = prop_info.get('default', 'None')
                    if isinstance(default, str):
                        default = f'"{default}"'
                    param_extractions.append(f'        {prop_name} = arguments.get("{prop_name}", {default})')
            
            # Generate function call
            param_names = list(func['input_schema']['properties'].keys())
            func_call = f'{func["name"]}({", ".join(param_names)})'
            
            param_block = '\n'.join(param_extractions)
            tool_case = f'''    elif name == "{func['name']}":
{param_block}
        
        try:
            result = {func_call}
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            return [TextContent(type="text", text=formatted_result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in {func['name']}: {{str(e)}}")]'''
            
            tool_cases.append(tool_case)
        
        function_names = [f'"{func["name"]}"' for func in self.functions]
        
        cases_block = '\n'.join(tool_cases)
        return f'''
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name not in [{", ".join(function_names)}]:
        raise ValueError(f"Unknown tool: {{name}}")
    
{cases_block}
'''
    
    def _generate_pydantic_models(self) -> str:
        """Generate Pydantic models for request validation."""
        models = []
        
        for func in self.functions:
            model_name = f"{func['name'].title().replace('_', '')}Request"
            
            fields = []
            for prop_name, prop_info in func['input_schema']['properties'].items():
                python_type = {
                    'string': 'str',
                    'integer': 'int', 
                    'number': 'float',
                    'boolean': 'bool',
                    'array': 'list',
                    'object': 'dict'
                }.get(prop_info['type'], 'str')
                
                if prop_name not in func['input_schema'].get('required', []):
                    python_type = f"Optional[{python_type}]"
                    default = prop_info.get('default', 'None')
                    if isinstance(default, str) and default != 'None':
                        default = f'"{default}"'
                    fields.append(f"    {prop_name}: {python_type} = {default}")
                else:
                    fields.append(f"    {prop_name}: {python_type}")
            
            fields_block = '\n'.join(fields)
            model = f'''
class {model_name}(BaseModel):
{fields_block}
'''
            models.append(model)
        
        return "\n".join(models)
    
    def _generate_manifest_endpoint(self) -> str:
        """Generate the manifest endpoint."""
        tools_manifest = []
        for func in self.functions:
            tool_manifest = {
                "name": func['name'],
                "description": func['description'],
                "inputSchema": func['input_schema']
            }
            tools_manifest.append(tool_manifest)
        
        manifest = {
            "schema_version": "1.0",
            "name": f"{self.module_name}-mcp",
            "description": f"Auto-generated MCP server from {self.module_name}",
            "version": "1.0.0",
            "tools": tools_manifest
        }
        
        return f'''
@app.get("/")
async def get_manifest():
    """Serve the MCP manifest."""
    manifest = {json.dumps(manifest, indent=4)}
    return JSONResponse(content=manifest)

@app.get("/manifest.json")
async def get_manifest_json():
    """Alternative manifest endpoint."""
    return await get_manifest()
'''
    
    def _generate_http_endpoints(self) -> str:
        """Generate HTTP endpoints for each function."""
        endpoints = []
        
        for func in self.functions:
            model_name = f"{func['name'].title().replace('_', '')}Request"
            
            # Generate parameter extraction
            param_names = list(func['input_schema']['properties'].keys())
            param_access = [f"request.{name}" for name in param_names]
            func_call = f'{func["name"]}({", ".join(param_access)})'
            
            endpoint = f'''
@app.post("/{func['name']}")
async def {func['name']}_endpoint(request: {model_name}):
    """{func['description']}"""
    try:
        result = {func_call}
        return JSONResponse(content={{"result": result}})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in {func['name']}: {{str(e)}}")
'''
            endpoints.append(endpoint)
        
        return "\n".join(endpoints)
    
    def generate_manifest_json(self) -> Dict[str, Any]:
        """Generate manifest.json file."""
        tools = []
        for func in self.functions:
            tools.append({
                "name": func['name'],
                "description": func['description']
            })
        
        return {
            "name": f"{self.module_name}-mcp",
            "version": "1.0.0",
            "description": f"Auto-generated MCP server from {self.module_name}",
            "author": "MCP Auto-Generator",
            "license": "MIT",
            "server": {
                "command": "python",
                "args": [f"{self.module_name}_mcp_server.py"],
                "env": {}
            },
            "tools": tools
        }


def main():
    """Main conversion function."""
    parser = argparse.ArgumentParser(description="Convert Python functions to MCP server")
    parser.add_argument("input_file", help="Python file with functions to convert")
    parser.add_argument("--output-dir", default="./", help="Output directory for generated files")
    parser.add_argument("--http-only", action="store_true", help="Generate only HTTP server")
    parser.add_argument("--stdio-only", action="store_true", help="Generate only stdio server")
    
    args = parser.parse_args()
    
    # Analyze the input file
    print(f"Analyzing {args.input_file}...")
    analyzer = FunctionAnalyzer(args.input_file)
    functions = analyzer.extract_functions()
    
    if not functions:
        print("No suitable functions found for MCP conversion!")
        return
    
    print(f"Found {len(functions)} functions to convert:")
    for func in functions:
        print(f"  - {func['name']}: {func['description']}")
    
    # Generate servers
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    module_name = Path(args.input_file).stem
    generator = MCPServerGenerator(args.input_file, functions)
    
    if not args.http_only:
        # Generate stdio server
        stdio_code = generator.generate_stdio_server()
        stdio_file = output_dir / f"{module_name}_mcp_server.py"
        with open(stdio_file, 'w', encoding='utf-8') as f:
            f.write(stdio_code)
        print(f"Generated stdio MCP server: {stdio_file}")
    
    if not args.stdio_only:
        # Generate HTTP server
        http_code = generator.generate_http_server()
        http_file = output_dir / f"{module_name}_http_mcp_server.py"
        with open(http_file, 'w', encoding='utf-8') as f:
            f.write(http_code)
        print(f"Generated HTTP MCP server: {http_file}")
    
    # Generate manifest
    manifest = generator.generate_manifest_json()
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated manifest: {manifest_file}")
    
    print("\nConversion complete! Next steps:")
    print("1. Install dependencies: pip install mcp fastapi uvicorn")
    print("2. Test the stdio server: python {}_mcp_server.py".format(module_name))
    print("3. Test the HTTP server: python {}_http_mcp_server.py".format(module_name))


if __name__ == "__main__":
    main()
