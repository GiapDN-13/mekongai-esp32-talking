package xiaozhi.modules.agent.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Stored chat history row ({@code ai_agent_chat_history}).
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@TableName(value = "ai_agent_chat_history")
public class AgentChatHistoryEntity {
    /**
     * Surrogate key.
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * Device MAC address.
     */
    @TableField(value = "mac_address")
    private String macAddress;

    /**
     * Agent id.
     */
    @TableField(value = "agent_id")
    private String agentId;

    /**
     * Session id.
     */
    @TableField(value = "session_id")
    private String sessionId;

    /**
     * Role: 1 user, 2 agent.
     */
    @TableField(value = "chat_type")
    private Byte chatType;

    /**
     * Message payload (text or JSON).
     */
    @TableField(value = "content")
    private String content;

    /**
     * Linked audio blob id.
     */
    @TableField(value = "audio_id")
    private String audioId;

    /**
     * Created at.
     */
    @TableField(value = "created_at")
    private Date createdAt;

    /**
     * Updated at.
     */
    @TableField(value = "updated_at")
    private Date updatedAt;
}
