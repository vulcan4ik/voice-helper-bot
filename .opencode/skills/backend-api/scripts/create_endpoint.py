#!/usr/bin/env python3
"""
Generate a new API endpoint with proper structure for the ClaudeCode Sentiment Monitor project.
Creates a Next.js 15 App Router API route with authentication, validation, and error handling.
"""

import os
import sys
from pathlib import Path

ROUTE_TEMPLATE = '''import {{ NextRequest, NextResponse }} from "next/server";
import {{ z }} from "zod";
{service_import}

// Request validation schema
const {schema_name} = z.object({{
  // TODO: Define request parameters
  param: z.string(),
}});

{auth_function}

export async function {method}(request: NextRequest) {{
  try {{
    {auth_check}

    // Parse and validate {param_location}
    {validation_code}

    // TODO: Call service layer for business logic
    {service_call}

    // Return response
    return NextResponse.json({{ success: true, data: result }}{cache_headers});
  }} catch (error) {{
    console.error("Error in {method} /api/{endpoint_path}:", error);

    if (error instanceof z.ZodError) {{
      return NextResponse.json(
        {{ error: "Invalid request", details: error.errors }},
        {{ status: 400 }}
      );
    }}

    return NextResponse.json(
      {{ error: "Internal server error" }},
      {{ status: 500 }}
    );
  }}
}}
'''

AUTH_FUNCTION = '''
function verifyAuth(request: NextRequest): boolean {
  const authHeader = request.headers.get("authorization");
  const token = authHeader?.replace("Bearer ", "");
  return token === process.env.CRON_SECRET;
}
'''

def create_endpoint(endpoint_path: str, method: str, protected: bool, working_dir: Path):
    """Create a new API endpoint file"""

    # Determine paths
    parts = endpoint_path.split("/")
    route_dir = working_dir / "app" / "api" / "/".join(parts)
    route_file = route_dir / "route.ts"

    # Create directory
    route_dir.mkdir(parents=True, exist_ok=True)

    # Determine template variables
    schema_name = "".join(p.capitalize() for p in parts) + "Schema"
    method_upper = method.upper()

    # Service import (example - user should customize)
    service_import = '// import { exampleService } from "@/lib/services/example.service";'

    # Auth check
    if protected:
        auth_check = '''if (!verifyAuth(request)) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    '''
    else:
        auth_check = ''

    # Validation code
    if method_upper == "GET":
        param_location = "query parameters"
        validation_code = '''const { searchParams } = new URL(request.url);
    const params = {}Schema.parse({
      param: searchParams.get("param"),
    });'''.format(schema_name[:-6])
    else:
        param_location = "request body"
        validation_code = '''const body = await request.json();
    const params = {}Schema.parse(body);'''.format(schema_name[:-6])

    # Service call
    service_call = '''// const result = await exampleService.doSomething(params.param);
    const result = { message: "TODO: Implement service call" };'''

    # Cache headers
    if method_upper == "GET":
        cache_headers = ''', {
      headers: {
        "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
      },
    }'''
    else:
        cache_headers = ''

    # Generate content
    content = ROUTE_TEMPLATE.format(
        method=method_upper,
        schema_name=schema_name,
        service_import=service_import,
        auth_function=AUTH_FUNCTION if protected else '',
        auth_check=auth_check,
        param_location=param_location,
        validation_code=validation_code,
        service_call=service_call,
        cache_headers=cache_headers,
        endpoint_path=endpoint_path,
    )

    # Write file
    with open(route_file, 'w') as f:
        f.write(content)

    print(f"✅ Created endpoint: {route_file}")
    print(f"   Method: {method_upper}")
    print(f"   Protected: {protected}")
    print(f"   URL: http://localhost:3000/api/{endpoint_path}")
    print()
    print("Next steps:")
    print("1. Customize the validation schema")
    print("2. Import and call the appropriate service")
    print("3. Update error handling as needed")
    print("4. Test the endpoint locally")

def main():
    if len(sys.argv) < 3:
        print("Usage: create_endpoint.py <endpoint-path> <method> [--protected]")
        print()
        print("Arguments:")
        print("  endpoint-path   Path segments (e.g., 'dashboard/data' or 'ingest/poll')")
        print("  method          HTTP method (GET or POST)")
        print("  --protected     Make endpoint require CRON_SECRET authentication")
        print()
        print("Examples:")
        print("  create_endpoint.py dashboard/stats GET")
        print("  create_endpoint.py ingest/refresh POST --protected")
        sys.exit(1)

    endpoint_path = sys.argv[1]
    method = sys.argv[2].upper()
    protected = "--protected" in sys.argv

    if method not in ["GET", "POST"]:
        print("Error: Method must be GET or POST")
        sys.exit(1)

    # Find project root (look for app directory)
    working_dir = Path.cwd()
    if not (working_dir / "app").exists():
        print("Error: Must run from project root (directory containing 'app/')")
        sys.exit(1)

    create_endpoint(endpoint_path, method, protected, working_dir)

if __name__ == "__main__":
    main()
