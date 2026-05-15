package xiaozhi.modules.agent.service.impl;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

import lombok.RequiredArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.modules.agent.dto.AgentChatHistoryDTO;
import xiaozhi.modules.agent.dto.AgentChatSummaryDTO;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentChatSummaryService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.vo.AgentInfoVO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.llm.service.LLMService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;

/**
 * Chat summarization into agent {@code summaryMemory} (ported from legacy Python helper).
 */
@Service
@RequiredArgsConstructor
public class AgentChatSummaryServiceImpl implements AgentChatSummaryService {

    private static final Logger log = LoggerFactory.getLogger(AgentChatSummaryServiceImpl.class);

    private final AgentChatHistoryService agentChatHistoryService;
    private final AgentService agentService;
    private final DeviceService deviceService;
    private final LLMService llmService;
    private final ModelConfigService modelConfigService;

    private static final int MAX_SUMMARY_LENGTH = 1800;
    private static final Pattern JSON_PATTERN = Pattern.compile("\\{.*?\\}", Pattern.DOTALL);
    private static final Pattern DEVICE_CONTROL_PATTERN = Pattern.compile(
            "\u8bbe\u5907\u63a7\u5236|\u8bbe\u5907\u64cd\u4f5c|\u63a7\u5236\u8bbe\u5907|\u8bbe\u5907\u72b6\u6001|"
                    + "device control|device operation|control device|device status",
            Pattern.CASE_INSENSITIVE);
    private static final Pattern WEATHER_PATTERN = Pattern.compile(
            "\u5929\u6c14|\u6e29\u5ea6|\u6e7f\u5ea6|\u964d\u96e8|\u6c14\u8c61|"
                    + "weather|temperature|humidity|rain|forecast",
            Pattern.CASE_INSENSITIVE);
    private static final Pattern DATE_PATTERN = Pattern.compile(
            "\u65e5\u671f|\u65f6\u95f4|\u661f\u671f|\u6708\u4efd|\u5e74\u4efd|"
                    + "date|time|week|month|year|calendar|clock",
            Pattern.CASE_INSENSITIVE);

    private static boolean isLlmFailurePlaceholder(String summary) {
        if (summary == null) {
            return false;
        }
        return summary.equals("\u670d\u52a1\u6682\u4e0d\u53ef\u7528") || summary.equals("\u603b\u7ed3\u751f\u6210\u5931\u8d25")
                || summary.equals("Service temporarily unavailable") || summary.equals("Summary generation failed");
    }

    private AgentChatSummaryDTO generateChatSummary(String sessionId) {
        try {
            System.out.println("Starting chat summary for session " + sessionId);

            List<AgentChatHistoryDTO> chatHistory = getChatHistoryBySessionId(sessionId);
            if (chatHistory == null || chatHistory.isEmpty()) {
                return new AgentChatSummaryDTO(sessionId, "No chat history for this session");
            }

            String agentId = getAgentIdFromSession(sessionId, chatHistory);
            if (StringUtils.isBlank(agentId)) {
                return new AgentChatSummaryDTO(sessionId, "Could not resolve agent for session");
            }

            List<String> meaningfulMessages = extractMeaningfulMessages(chatHistory);
            if (meaningfulMessages.isEmpty()) {
                return new AgentChatSummaryDTO(sessionId, "No meaningful user messages to summarize");
            }

            String summary = generateSummaryFromMessages(meaningfulMessages, agentId);

            log.info("Chat summary generated for session {}, length={} chars", sessionId, summary.length());
            return new AgentChatSummaryDTO(sessionId, agentId, summary);

        } catch (Exception e) {
            log.error("Chat summary failed for session {}: {}", sessionId, e.getMessage());
            return new AgentChatSummaryDTO(sessionId, "Summary error: " + e.getMessage());
        }
    }

    @Override
    public boolean generateAndSaveChatSummary(String sessionId) {
        try {
            DeviceEntity device = getDeviceBySessionId(sessionId);
            if (device == null) {
                log.info("No device linked to session {}", sessionId);
                return false;
            }

            String memModelId = agentService.getAgentById(device.getAgentId()).getMemModelId();
            if (memModelId != null && memModelId.equals(Constant.MEMORY_MEM_REPORT_ONLY)) {
                log.info("Session {} uses report-only memory; skip summary", sessionId);
                return true;
            }

            AgentChatSummaryDTO summaryDTO = generateChatSummary(sessionId);
            if (!summaryDTO.isSuccess()) {
                log.info("Summary generation failed: {}", summaryDTO.getErrorMessage());
                return false;
            }

            agentService.updateAgentById(device.getAgentId(),
                    new AgentUpdateDTO() {
                        {
                            setSummaryMemory(summaryDTO.getSummary());
                        }
                    });

            log.info("Saved chat summary for session {} to agent {}", sessionId, device.getAgentId());
            return true;

        } catch (Exception e) {
            log.error("Persist chat summary failed for session {}: {}", sessionId, e.getMessage());
            return false;
        }
    }

    private List<AgentChatHistoryDTO> getChatHistoryBySessionId(String sessionId) {
        try {
            String agentId = findAgentIdBySessionId(sessionId);
            if (StringUtils.isBlank(agentId)) {
                return null;
            }
            return agentChatHistoryService.getChatHistoryBySessionId(agentId, sessionId);
        } catch (Exception e) {
            log.error("Load chat history failed for session {}: {}", sessionId, e.getMessage());
            return null;
        }
    }

    private String findAgentIdBySessionId(String sessionId) {
        try {
            QueryWrapper<AgentChatHistoryEntity> wrapper = new QueryWrapper<>();
            wrapper.select("agent_id")
                    .eq("session_id", sessionId)
                    .last("LIMIT 1");

            AgentChatHistoryEntity entity = agentChatHistoryService.getOne(wrapper);
            return entity != null ? entity.getAgentId() : null;
        } catch (Exception e) {
            log.error("Resolve agentId for session {} failed: {}", sessionId, e.getMessage());
            return null;
        }
    }

    private String getAgentIdFromSession(String sessionId, List<AgentChatHistoryDTO> chatHistory) {
        return findAgentIdBySessionId(sessionId);
    }

    private List<String> extractMeaningfulMessages(List<AgentChatHistoryDTO> chatHistory) {
        List<String> meaningfulMessages = new ArrayList<>();

        for (AgentChatHistoryDTO message : chatHistory) {
            if (message.getChatType() != null && message.getChatType() == 1) {
                String content = extractContentFromMessage(message);
                if (isMeaningfulMessage(content)) {
                    meaningfulMessages.add(content);
                }
            }
        }

        return meaningfulMessages;
    }

    private String extractContentFromMessage(AgentChatHistoryDTO message) {
        String content = message.getContent();
        if (StringUtils.isBlank(content)) {
            return "";
        }

        Matcher matcher = JSON_PATTERN.matcher(content);
        if (matcher.find()) {
            String jsonContent = matcher.group();
            return extractTextFromJson(jsonContent);
        }

        return content;
    }

    private String extractTextFromJson(String jsonContent) {
        Pattern contentPattern = Pattern.compile("\"content\"\\s*:\\s*\"([^\"]*)\"");
        Matcher matcher = contentPattern.matcher(jsonContent);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return jsonContent;
    }

    private boolean isMeaningfulMessage(String content) {
        if (StringUtils.isBlank(content)) {
            return false;
        }

        if (DEVICE_CONTROL_PATTERN.matcher(content).find()) {
            return false;
        }

        if (WEATHER_PATTERN.matcher(content).find() || DATE_PATTERN.matcher(content).find()) {
            return false;
        }

        return content.length() >= 5;
    }

    private String generateSummaryFromMessages(List<String> messages, String agentId) {
        if (messages.isEmpty()) {
            return "Too little in this chat to summarize.";
        }

        StringBuilder conversation = new StringBuilder();
        for (int i = 0; i < messages.size(); i++) {
            conversation.append("Message ").append(i + 1).append(": ").append(messages.get(i)).append("\n");
        }

        try {
            String historyMemory = getCurrentAgentMemory(agentId);

            String summary = callJavaLLMForSummaryWithHistory(conversation.toString(), historyMemory, agentId);

            if (summary.length() > MAX_SUMMARY_LENGTH) {
                summary = summary.substring(0, MAX_SUMMARY_LENGTH) + "...";
            }

            return summary;
        } catch (Exception e) {
            log.error("LLM summary call failed: {}", e.getMessage());
            throw new RuntimeException("LLM unavailable; cannot build chat summary");
        }
    }

    private String getCurrentAgentMemory(String agentId) {
        try {
            if (StringUtils.isBlank(agentId)) {
                return null;
            }

            AgentInfoVO agentInfo = agentService.getAgentById(agentId);
            if (agentInfo == null) {
                return null;
            }

            return agentInfo.getSummaryMemory();
        } catch (Exception e) {
            log.error("Load agent memory failed, agentId={}: {}", agentId, e.getMessage());
            return null;
        }
    }

    private String callJavaLLMForSummaryWithHistory(String conversation, String historyMemory, String agentId) {
        try {
            String modelId = getMemorySummaryModelId(agentId);

            if (StringUtils.isBlank(modelId)) {
                log.info("No memory-summary model id; using default LLM");
                return llmService.generateSummaryWithHistory(conversation, historyMemory, null, null);
            }

            String summary = llmService.generateSummaryWithHistory(conversation, historyMemory, null, modelId);

            if (StringUtils.isNotBlank(summary) && !isLlmFailurePlaceholder(summary)) {
                return summary;
            }

            throw new RuntimeException("LLM returned failure token: " + summary);

        } catch (Exception e) {
            log.error("LLM summary (with history) error, agentId={}: {}", agentId, e.getMessage());
            throw e;
        }
    }

    private String callJavaLLMForSummary(String conversation, String agentId) {
        try {
            String modelId = getMemorySummaryModelId(agentId);

            if (StringUtils.isBlank(modelId)) {
                log.info("No memory-summary model id; using default LLM");
                return llmService.generateSummary(conversation);
            }

            String summary = llmService.generateSummaryWithModel(conversation, modelId);

            if (StringUtils.isNotBlank(summary) && !isLlmFailurePlaceholder(summary)) {
                return summary;
            }

            throw new RuntimeException("LLM returned failure token: " + summary);

        } catch (Exception e) {
            log.error("LLM summary error, agentId={}: {}", agentId, e.getMessage());
            throw e;
        }
    }

    private String getMemorySummaryModelId(String agentId) {
        try {
            if (StringUtils.isBlank(agentId)) {
                return null;
            }

            AgentInfoVO agentInfo = agentService.getAgentById(agentId);
            if (agentInfo == null) {
                return null;
            }

            String memModelId = agentInfo.getMemModelId();
            if (StringUtils.isBlank(memModelId)) {
                return null;
            }

            ModelConfigEntity memModelConfig = modelConfigService.getModelByIdFromCache(memModelId);
            if (memModelConfig == null || memModelConfig.getConfigJson() == null) {
                return null;
            }

            Map<String, Object> configMap = memModelConfig.getConfigJson();
            String llmModelId = (String) configMap.get("llm");

            if (StringUtils.isBlank(llmModelId)) {
                return agentInfo.getLlmModelId();
            }

            return llmModelId;
        } catch (Exception e) {
            log.error("Resolve memory-summary LLM id failed, agentId={}: {}", agentId, e.getMessage());
            return null;
        }
    }

    private DeviceEntity getDeviceBySessionId(String sessionId) {
        try {
            QueryWrapper<AgentChatHistoryEntity> wrapper = new QueryWrapper<>();
            wrapper.select("mac_address")
                    .eq("session_id", sessionId)
                    .last("LIMIT 1");

            AgentChatHistoryEntity entity = agentChatHistoryService.getOne(wrapper);
            if (entity != null && StringUtils.isNotBlank(entity.getMacAddress())) {
                return deviceService.getDeviceByMacAddress(entity.getMacAddress());
            }
            return null;
        } catch (Exception e) {
            log.error("Resolve device for session {} failed: {}", sessionId, e.getMessage());
            return null;
        }
    }
}
