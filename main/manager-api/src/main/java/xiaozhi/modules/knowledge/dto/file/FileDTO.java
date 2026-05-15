package xiaozhi.modules.knowledge.dto.file;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * File manager aggregate DTO (RAGFlow-style file APIs).
 */
@Schema(description = "File module aggregate DTO")
public class FileDTO {

    // --- Requests ---

    /** Upload file (upload). */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "File upload request")
    public static class UploadReq implements Serializable {

        @NotNull(message = "File is required")
        @Schema(description = "Multipart file body", requiredMode = Schema.RequiredMode.REQUIRED)
        private MultipartFile file;

        @Schema(description = "Parent folder id (root if empty)", example = "folder_001")
        @JsonProperty("parent_id")
        private String parentId;
    }

    /** Create folder. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Create folder request")
    public static class CreateReq implements Serializable {

        @NotBlank(message = "Folder name is required")
        @Schema(description = "Folder name", requiredMode = Schema.RequiredMode.REQUIRED, example = "New folder")
        private String name;

        @Schema(description = "Parent folder id (root if empty)", example = "folder_001")
        @JsonProperty("parent_id")
        private String parentId;

        @NotBlank(message = "Type is required")
        @Schema(description = "Type: FOLDER", requiredMode = Schema.RequiredMode.REQUIRED, example = "FOLDER")
        @Builder.Default
        private String type = "FOLDER";
    }

    /** Rename file or folder. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Rename request")
    public static class RenameReq implements Serializable {

        @NotBlank(message = "File id is required")
        @Schema(description = "File or folder id", requiredMode = Schema.RequiredMode.REQUIRED, example = "file_001")
        @JsonProperty("file_id")
        private String fileId;

        @NotBlank(message = "New name is required")
        @Schema(description = "New name", requiredMode = Schema.RequiredMode.REQUIRED, example = "Renamed file")
        private String name;
    }

    /** Move entries. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Move request")
    public static class MoveReq implements Serializable {

        @NotEmpty(message = "Source ids are required")
        @Schema(description = "Source file/folder ids", requiredMode = Schema.RequiredMode.REQUIRED, example = "[\"file_001\", \"file_002\"]")
        @JsonProperty("src_file_ids")
        private List<String> srcFileIds;

        @NotBlank(message = "Target folder id is required")
        @Schema(description = "Destination folder id", requiredMode = Schema.RequiredMode.REQUIRED, example = "folder_002")
        @JsonProperty("dest_file_id")
        private String destFileId;
    }

    /** Batch delete. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Batch delete request")
    public static class RemoveReq implements Serializable {

        @NotEmpty(message = "File ids are required")
        @Schema(description = "File or folder ids", requiredMode = Schema.RequiredMode.REQUIRED, example = "[\"file_001\", \"file_002\"]")
        @JsonProperty("file_ids")
        private List<String> fileIds;
    }

    /** Import files into knowledge bases. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Import to knowledge bases request")
    public static class ConvertReq implements Serializable {

        @NotEmpty(message = "File ids are required")
        @Schema(description = "Source file ids", requiredMode = Schema.RequiredMode.REQUIRED, example = "[\"file_001\", \"file_002\"]")
        @JsonProperty("file_ids")
        private List<String> fileIds;

        @NotEmpty(message = "Dataset id list is required")
        @Schema(description = "Target dataset ids", requiredMode = Schema.RequiredMode.REQUIRED, example = "[\"kb_001\"]")
        @JsonProperty("kb_ids")
        private List<String> kbIds;
    }

    /** List files under a folder. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "List files request")
    public static class ListReq implements Serializable {

        @Schema(description = "Parent folder id (root if empty)", example = "folder_001")
        @JsonProperty("parent_id")
        private String parentId;

        @Schema(description = "Keyword filter", example = "report")
        private String keywords;

        @Schema(description = "Page number (1-based)", example = "1")
        private Integer page;

        @Schema(description = "Page size", example = "30")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Sort field: create_time / update_time / name / size", example = "create_time")
        private String orderby;

        @Schema(description = "Descending sort", example = "true")
        private Boolean desc;
    }

    // --- Responses ---

    /** File or folder row. */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "File or folder info")
    public static class InfoVO implements Serializable {

        @Schema(description = "Node id", example = "file_001")
        private String id;

        @Schema(description = "Parent folder id", example = "folder_001")
        @JsonProperty("parent_id")
        private String parentId;

        @Schema(description = "Tenant id", example = "tenant_001")
        @JsonProperty("tenant_id")
        private String tenantId;

        @Schema(description = "Creator id", example = "user_001")
        @JsonProperty("created_by")
        private String createdBy;

        @Schema(description = "Type: FOLDER / FILE", example = "FOLDER")
        private String type;

        @Schema(description = "Display name", example = "My folder")
        private String name;

        @Schema(description = "Path", example = "/root/folder")
        private String location;

        @Schema(description = "Size in bytes", example = "1024")
        private Long size;

        @Schema(description = "Source type", example = "local")
        @JsonProperty("source_type")
        private String sourceType;

        @Schema(description = "Created at (epoch ms)", example = "1700000000000")
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Created at (formatted)", example = "2024-01-15 10:30:00")
        @JsonProperty("create_date")
        private String createDate;

        @Schema(description = "Updated at (epoch ms)", example = "1700000001000")
        @JsonProperty("update_time")
        private Long updateTime;

        @Schema(description = "Updated at (formatted)", example = "2024-01-15 11:00:00")
        @JsonProperty("update_date")
        private String updateDate;

        @Schema(description = "Extension", example = "pdf")
        private String extension;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "File list response")
    public static class ListVO implements Serializable {

        @Schema(description = "Total rows", example = "100")
        private Long total;

        @Schema(description = "Current parent folder")
        @JsonProperty("parent_folder")
        private InfoVO parentFolder;

        @Schema(description = "Files and folders")
        private List<InfoVO> files;

        @Schema(description = "Breadcrumb trail")
        private List<InfoVO> breadcrumb;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Convert job row")
    public static class ConvertVO implements Serializable {

        @Schema(description = "Convert job id", example = "convert_001")
        private String id;

        @Schema(description = "Source file id", example = "file_001")
        @JsonProperty("file_id")
        private String fileId;

        @Schema(description = "Target document id", example = "doc_001")
        @JsonProperty("document_id")
        private String documentId;

        @Schema(description = "Created at (epoch ms)", example = "1700000000000")
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Created at (formatted)", example = "2024-01-15 10:30:00")
        @JsonProperty("create_date")
        private String createDate;

        @Schema(description = "Updated at (epoch ms)", example = "1700000001000")
        @JsonProperty("update_time")
        private Long updateTime;

        @Schema(description = "Updated at (formatted)", example = "2024-01-15 11:00:00")
        @JsonProperty("update_date")
        private String updateDate;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Convert job status")
    public static class ConvertStatusVO implements Serializable {

        @Schema(description = "Status: pending / processing / completed / failed", example = "completed")
        private String status;

        @Schema(description = "Progress 0.0–1.0", example = "1.0")
        private Float progress;

        @Schema(description = "Status message", example = "Completed")
        private String message;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Breadcrumb (all parents)")
    public static class BreadcrumbVO implements Serializable {

        @Schema(description = "Parents root → current")
        @JsonProperty("parent_folders")
        private List<InfoVO> parentFolders;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Root folder info")
    public static class RootFolderVO implements Serializable {

        @Schema(description = "Root folder")
        @JsonProperty("root_folder")
        private InfoVO rootFolder;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Schema(description = "Parent folder info")
    public static class ParentFolderVO implements Serializable {

        @Schema(description = "Parent folder")
        @JsonProperty("parent_folder")
        private InfoVO parentFolder;
    }
}
