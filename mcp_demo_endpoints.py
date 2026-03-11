"""
Demo endpoints for testing MCP integration.
Add these to app.py to verify MCP servers are working.
"""

# Add after the other API routes in app.py:

@app.route('/api/mcp/time', methods=['GET'])
def mcp_get_time():
    """Test MCP Time server - get current time."""
    if not mcp_manager:
        return jsonify({'error': 'MCP not available'}), 503
    
    try:
        result = mcp_manager.call_tool_sync('time', 'get_current_time', {})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mcp/memory/create', methods=['POST'])
def mcp_create_memory():
    """Test MCP Memory server - create entities."""
    if not mcp_manager:
        return jsonify({'error': 'MCP not available'}), 503
    
    data = request.get_json()
    entities = data.get('entities', [])
    
    try:
        result = mcp_manager.call_tool_sync('memory', 'create_entities', {'entities': entities})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mcp/memory/graph', methods=['GET'])
def mcp_read_graph():
    """Test MCP Memory server - read knowledge graph."""
    if not mcp_manager:
        return jsonify({'error': 'MCP not available'}), 503
    
    try:
        result = mcp_manager.call_tool_sync('memory', 'read_graph', {})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
