package xiaozhi.modules.agent.service.biz.impl;

import java.util.Base64;
import java.util.Date;
import java.util.Objects;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.agent.dto.AgentChatHistoryReportDTO;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.service.AgentChatAudioService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentChatSummaryService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.biz.AgentChatHistoryBizService;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;

/**
 * {@link AgentChatHistoryBizService} impl
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class AgentChatHistoryBizServiceImpl implements AgentChatHistoryBizService {
    private final AgentService agentService;
    private final AgentChatHistoryService agentChatHistoryService;
    private final AgentChatAudioService agentChatAudioService;
    private final AgentChatSummaryService agentChatSummaryService;
    private final RedisUtils redisUtils;
    private final DeviceService deviceService;

    /**
     * Persist chat report: optional Opus upload plus history row.
     *
     * @param report device payload
     * @return {@code true} if accepted
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Boolean report(AgentChatHistoryReportDTO report) {
        String macAddress = report.getMacAddress();
        Byte chatType = report.getChatType();
        Long reportTimeMillis = null != report.getReportTime() ? report.getReportTime() * 1000
                : System.currentTimeMillis();
        log.info("Device chat report: macAddress={}, type={} reportTime={}", macAddress, chatType, reportTimeMillis);

        AgentEntity agentEntity = agentService.getDefaultAgentByMacAddress(macAddress);
        if (agentEntity == null) {
            return Boolean.FALSE;
        }

        Integer chatHistoryConf = agentEntity.getChatHistoryConf();
        String agentId = agentEntity.getId();

        if (Objects.equals(chatHistoryConf, Constant.ChatHistoryConfEnum.RECORD_TEXT.getCode())) {
            saveChatText(report, agentId, macAddress, null, reportTimeMillis);
        } else if (Objects.equals(chatHistoryConf, Constant.ChatHistoryConfEnum.RECORD_TEXT_AUDIO.getCode())) {
            String audioId = saveChatAudio(report);
            saveChatText(report, agentId, macAddress, audioId, reportTimeMillis);
        }

        redisUtils.set(RedisKeys.getAgentDeviceLastConnectedAtById(agentId), new Date());

        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device != null) {
            deviceService.updateDeviceConnectionInfo(agentId, device.getId(), null);
        } else {
            log.warn("Chat report: no device row for mac {}", macAddress);
        }

        return Boolean.TRUE;
    }

    /**
     * Decode {@code report.getAudioBase64()} and store in {@code ai_agent_chat_audio}.
     */
    private String saveChatAudio(AgentChatHistoryReportDTO report) {
        String audioId = null;

        if (report.getAudioBase64() != null && !report.getAudioBase64().isEmpty()) {
            try {
                byte[] audioData = Base64.getDecoder().decode(report.getAudioBase64());
                audioId = agentChatAudioService.saveAudio(audioData);
                log.info("Audio saved, audioId={}", audioId);
            } catch (Exception e) {
                log.error("Audio save failed", e);
                return null;
            }
        }
        return audioId;
    }

    /**
     * Build and insert {@link AgentChatHistoryEntity}.
     */
    private void saveChatText(AgentChatHistoryReportDTO report, String agentId, String macAddress, String audioId,
            Long reportTime) {
        AgentChatHistoryEntity entity = AgentChatHistoryEntity.builder()
                .macAddress(macAddress)
                .agentId(agentId)
                .sessionId(report.getSessionId())
                .chatType(report.getChatType())
                .content(report.getContent())
                .audioId(audioId)
                .createdAt(new Date(reportTime))
                // NOTE(haotian): 2025/5/26 omit updatedAt on purpose; createdAt reflects ingest delay
                .build();

        agentChatHistoryService.save(entity);

        log.info("Chat report stored: device {} agent {}", macAddress, agentId);
    }
}
