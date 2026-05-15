package xiaozhi.modules.agent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

/**
 * Opus audio payload for chat ({@code ai_agent_chat_audio}).
 *
 * @author Goody
 * @version 1.0, 2025/5/8
 * @since 1.0.0
 */
@Data
@TableName("ai_agent_chat_audio")
public class AgentChatAudioEntity {
    /**
     * Audio row id.
     */
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    /**
     * Raw Opus bytes.
     */
    private byte[] audio;
}