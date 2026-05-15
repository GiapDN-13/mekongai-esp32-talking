package xiaozhi.modules.agent.service;


import java.util.List;

/**
 * MCP WebSocket URL and tool discovery for an agent.
 *
 * @author zjy
 */
public interface AgentMcpAccessPointService {
    /**
     * Signed MCP access URL for the agent.
     * @param id agent id
     * @return ws/wss URL
     */
   String getAgentMcpAccessAddress(String id);

    /**
     * Tool names exposed by the agent MCP endpoint.
     * @param id agent id
     * @return tool names
     */
   List<String> getAgentMcpToolsList(String id);
}
