package xiaozhi.modules.agent.vo;

import lombok.Data;

import java.util.Date;

/**
 * Voice-print row for list APIs.
 */
@Data
public class AgentVoicePrintVO {

    /**
     * Row id.
     */
    private String id;
    /**
     * Audio file id.
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
     * Created at.
     */
    private Date createDate;
}
