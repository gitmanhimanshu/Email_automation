"""Hosted multi-user MCP server, connected from claude.ai / ChatGPT over HTTPS.

Different from mcp_server/, which is the single-user stdio server that runs on
your own laptop. This one holds no credentials of its own: each request carries
the calling user's Google access token, obtained through the OAuth proxy.
"""
