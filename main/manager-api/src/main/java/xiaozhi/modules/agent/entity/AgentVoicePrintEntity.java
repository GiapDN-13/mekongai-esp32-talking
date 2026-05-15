package xiaozhi.modules.agent.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

/**
 * Agent voice-print enrollment row.
 *
 * @author zjy
 */
@TableName(value = "ai_agent_voice_print")
@Data
public class AgentVoicePrintEntity {
    /**
     * Row id.
     */
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;
    /**
     * Agent id.
     */
    private String agentId;
    /**
     * Linked audio id.
     */
    private String audioId;
    /**
     * Speaker display name.
     */
    private String sourceName;
    /**
     * Speaker description.
     */
    private String introduce;

    /**
     * Creator user id.
     */
    @TableField(fill = FieldFill.INSERT)
    private Long creator;
    /**
     * Created at.
     */
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;

    /**
     * Last updater user id.
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Long updater;
    /**
     * Updated at.
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Date updateDate;
}
