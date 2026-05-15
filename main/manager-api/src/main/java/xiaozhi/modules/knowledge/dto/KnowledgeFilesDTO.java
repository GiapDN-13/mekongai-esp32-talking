package xiaozhi.modules.knowledge.dto;

import java.io.Serial;
import java.io.Serializable;
import java.util.Date;
import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

@Data
@Schema(description = "Knowledge base document")
@JsonIgnoreProperties(ignoreUnknown = true)
public class KnowledgeFilesDTO implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;
    @Schema(description = "Primary id exposed to UI (remote document id)")
    private String id;

    @Schema(description = "RAGFlow document id")
    private String documentId;

    @Schema(description = "Dataset id")
    private String datasetId;

    @Schema(description = "File name")
    private String name;

    @Schema(description = "MIME-ish file type")
    private String fileType;

    @Schema(description = "Size in bytes")
    private Long fileSize;

    @Schema(description = "Storage path or locator")
    private String filePath;

    @Schema(description = "Parse progress 0.0–1.0")
    private Double progress;

    @Schema(description = "Thumbnail Base64 or URL")
    private String thumbnail;

    @Schema(description = "Parse duration in seconds")
    private Double processDuration;

    @Schema(description = "Source type: local, s3, url, ...")
    private String sourceType;

    @Schema(description = "Custom metadata map")
    private Map<String, Object> metaFields;

    @Schema(description = "Chunk method")
    private String chunkMethod;

    @Schema(description = "Parser config map")
    private Map<String, Object> parserConfig;

    @Schema(description = "Availability: 1 normal, 0 disabled")
    private String status;

    @Schema(description = "Run state: UNSTART / RUNNING / CANCEL / DONE / FAIL")
    private String run;

    @Schema(description = "Creator user id")
    private Long creator;

    @Schema(description = "Created at")
    private Date createdAt;

    @Schema(description = "Last updater user id")
    private Long updater;

    @Schema(description = "Updated at")
    private Date updatedAt;

    @Schema(description = "Chunk count")
    private Integer chunkCount;

    @Schema(description = "Token count")
    private Long tokenCount;

    @Schema(description = "Parse error or progress message")
    private String error;

    private static final Integer STATUS_UNSTART = 0;
    private static final Integer STATUS_RUNNING = 1;
    private static final Integer STATUS_CANCEL = 2;
    private static final Integer STATUS_DONE = 3;
    private static final Integer STATUS_FAIL = 4;

    /** UI status code derived from {@link #run}. */
    public Integer getParseStatusCode() {
        if (run == null) {
            return STATUS_UNSTART;
        }

        switch (run.toUpperCase()) {
            case "RUNNING":
                return STATUS_RUNNING;
            case "CANCEL":
                return STATUS_CANCEL;
            case "DONE":
                return STATUS_DONE;
            case "FAIL":
                return STATUS_FAIL;
            case "UNSTART":
            default:
                return STATUS_UNSTART;
        }
    }

}
