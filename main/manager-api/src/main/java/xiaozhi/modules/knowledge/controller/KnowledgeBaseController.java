package xiaozhi.modules.knowledge.controller;

import java.util.*;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.common.utils.ToolUtil;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.knowledge.service.KnowledgeManagerService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.security.user.SecurityUser;

@AllArgsConstructor
@RestController
@RequestMapping("/datasets")
@Tag(name = "Knowledge bases")
public class KnowledgeBaseController {

    private final KnowledgeBaseService knowledgeBaseService;
    private final KnowledgeManagerService knowledgeManagerService;

    @GetMapping
    @Operation(summary = "Paged knowledge base list")
    @RequiresPermissions("sys:role:normal")
    public Result<PageData<KnowledgeBaseDTO>> getPageList(
            @RequestParam(required = false) String name,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "10") Integer page_size) {
        Long currentUserId = SecurityUser.getUserId();

        KnowledgeBaseDTO knowledgeBaseDTO = new KnowledgeBaseDTO();
        knowledgeBaseDTO.setName(name);
        knowledgeBaseDTO.setCreator(currentUserId);

        PageData<KnowledgeBaseDTO> pageData = knowledgeBaseService.getPageList(knowledgeBaseDTO, page, page_size);
        return new Result<PageData<KnowledgeBaseDTO>>().ok(pageData);
    }

    @GetMapping("/{dataset_id}")
    @Operation(summary = "Get knowledge base by dataset id")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeBaseDTO> getByDatasetId(@PathVariable("dataset_id") String datasetId) {
        Long currentUserId = SecurityUser.getUserId();

        KnowledgeBaseDTO knowledgeBaseDTO = knowledgeBaseService.getByDatasetId(datasetId);

        if (knowledgeBaseDTO.getCreator() == null || !knowledgeBaseDTO.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        return new Result<KnowledgeBaseDTO>().ok(knowledgeBaseDTO);
    }

    @PostMapping
    @Operation(summary = "Create knowledge base")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeBaseDTO> save(@RequestBody @Validated KnowledgeBaseDTO knowledgeBaseDTO) {
        KnowledgeBaseDTO resp = knowledgeBaseService.save(knowledgeBaseDTO);
        return new Result<KnowledgeBaseDTO>().ok(resp);
    }

    @PutMapping("/{dataset_id}")
    @Operation(summary = "Update knowledge base")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeBaseDTO> update(@PathVariable("dataset_id") String datasetId,
            @RequestBody @Validated KnowledgeBaseDTO knowledgeBaseDTO) {
        Long currentUserId = SecurityUser.getUserId();

        KnowledgeBaseDTO existingKnowledgeBase = knowledgeBaseService.getByDatasetId(datasetId);

        if (existingKnowledgeBase.getCreator() == null || !existingKnowledgeBase.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        knowledgeBaseDTO.setId(existingKnowledgeBase.getId());
        knowledgeBaseDTO.setDatasetId(datasetId);
        KnowledgeBaseDTO resp = knowledgeBaseService.update(knowledgeBaseDTO);
        return new Result<KnowledgeBaseDTO>().ok(resp);
    }

    @DeleteMapping("/{dataset_id}")
    @Operation(summary = "Delete one knowledge base")
    @Parameter(name = "dataset_id", description = "Dataset id", required = true)
    @RequiresPermissions("sys:role:normal")
    public Result<Void> delete(@PathVariable("dataset_id") String datasetId) {
        Long currentUserId = SecurityUser.getUserId();

        KnowledgeBaseDTO existingKnowledgeBase = knowledgeBaseService.getByDatasetId(datasetId);

        if (existingKnowledgeBase.getCreator() == null || !existingKnowledgeBase.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        knowledgeManagerService.deleteDatasetWithFiles(datasetId);
        return new Result<>();
    }

    @DeleteMapping("/batch")
    @Operation(summary = "Batch delete knowledge bases")
    @Parameter(name = "ids", description = "Comma-separated dataset ids", required = true)
    @RequiresPermissions("sys:role:normal")
    public Result<Void> deleteBatch(@RequestParam("ids") String ids) {
        if (StringUtils.isBlank(ids)) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }

        Long currentUserId = SecurityUser.getUserId();
        List<String> idList = Arrays.asList(ids.split(","));
        List<KnowledgeBaseDTO> knowledgeBaseDTOs = Optional.ofNullable(knowledgeBaseService.getByDatasetIdList(idList))
                .orElseGet(ArrayList::new);
        if (ToolUtil.isNotEmpty(knowledgeBaseDTOs)) {
            knowledgeBaseDTOs.forEach(item -> {
                if (item.getCreator() == null || !item.getCreator().equals(currentUserId)) {
                    throw new RenException(ErrorCode.NO_PERMISSION);
                }
                knowledgeManagerService.deleteDatasetWithFiles(item.getDatasetId());
            });
        }
        return new Result<>();
    }

    @GetMapping("/rag-models")
    @Operation(summary = "List RAG model configs")
    @RequiresPermissions("sys:role:normal")
    public Result<List<ModelConfigEntity>> getRAGModels() {
        List<ModelConfigEntity> result = knowledgeBaseService.getRAGModels();
        return new Result<List<ModelConfigEntity>>().ok(result);
    }
}
