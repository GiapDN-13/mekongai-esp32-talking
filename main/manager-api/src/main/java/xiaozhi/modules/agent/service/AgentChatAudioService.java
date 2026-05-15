package xiaozhi.modules.agent.service;

import com.baomidou.mybatisplus.extension.service.IService;

import xiaozhi.modules.agent.entity.AgentChatAudioEntity;

/**
 * Opus blob storage for chat audio.
 *
 * @author Goody
 * @version 1.0, 2025/5/8
 * @since 1.0.0
 */
public interface AgentChatAudioService extends IService<AgentChatAudioEntity> {
    /**
     * Store bytes and return generated id.
     *
     * @param audioData opus payload
     * @return audio id
     */
    String saveAudio(byte[] audioData);

    /**
     * Load blob by id.
     *
     * @param audioId id
     * @return bytes or null
     */
    byte[] getAudio(String audioId);
}
