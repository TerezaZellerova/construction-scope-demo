"""One stdio process per trusted host identity. Identity is not a tool argument."""
import os
from mcp.server.fastmcp import FastMCP
import core
import security

security.validate_configuration()
core.initialize()
mcp = FastMCP('Construction scope assistant')
def identity():
    # Revalidated on every call. Configure in trusted MCP host, never in model input.
    return core.authenticate(os.getenv('MCP_DEMO_TOKEN',''))

@mcp.tool()
def list_authorized_projects() -> list[dict]:
    return core.list_projects(identity())

@mcp.tool()
def retrieve_project_documents(project_id: str) -> list[dict]:
    return core.documents(identity(),project_id)

@mcp.tool()
async def generate_scope_review(project_id: str) -> dict:
    return await core.generate(identity(),project_id)

@mcp.tool()
def save_approved_report(project_id: str, review_id: str, request_key: str) -> dict:
    return core.save(identity(),project_id,review_id,request_key)

if __name__ == '__main__': mcp.run(transport='stdio')
