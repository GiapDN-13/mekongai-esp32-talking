package xiaozhi.modules.agent.controller;

import java.util.List;
import java.util.Map;

import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.Result;
import xiaozhi.common.utils.ResultUtils;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.agent.vo.AgentTemplateVO;

@Tag(name = "Agent templates")
@AllArgsConstructor
@RestController
@RequestMapping("/agent/template")
public class AgentTemplateController {
    
    private final AgentTemplateService agentTemplateService;
    
    @GetMapping("/page")
    @Operation(summary = "Paged agent templates")
    @RequiresPermissions("sys:role:superAdmin")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "Page number (1-based)", required = true),
            @Parameter(name = Constant.LIMIT, description = "Page size", required = true),
            @Parameter(name = "agentName", description = "Template name (LIKE filter)")
    })
    public Result<PageData<AgentTemplateVO>> getAgentTemplatesPage(
            @Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        
        // MyBatis-Plus page
        int page = Integer.parseInt(params.getOrDefault(Constant.PAGE, "1").toString());
        int limit = Integer.parseInt(params.getOrDefault(Constant.LIMIT, "10").toString());
        Page<AgentTemplateEntity> pageInfo = new Page<>(page, limit);
        
        // Query wrapper
        QueryWrapper<AgentTemplateEntity> wrapper = new QueryWrapper<>();
        String agentName = (String) params.get("agentName");
        if (agentName != null && !agentName.isEmpty()) {
            wrapper.like("agent_name", agentName);
        }
        wrapper.orderByAsc("sort");
        
        // Query
        IPage<AgentTemplateEntity> pageResult = agentTemplateService.page(pageInfo, wrapper);
        
        // Entity → VO
        List<AgentTemplateVO> voList = ConvertUtils.sourceToTarget(pageResult.getRecords(), AgentTemplateVO.class);

        // PageData(total, list)
        PageData<AgentTemplateVO> pageData = new PageData<>(voList, pageResult.getTotal());

        return new Result<PageData<AgentTemplateVO>>().ok(pageData);
    }
    
    @GetMapping("/{id}")
    @Operation(summary = "Get template by id")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<AgentTemplateVO> getAgentTemplateById(@PathVariable("id") String id) {
        AgentTemplateEntity template = agentTemplateService.getById(id);
        if (template == null) {
            return ResultUtils.error("Template not found");
        }
        
        AgentTemplateVO vo = ConvertUtils.sourceToTarget(template, AgentTemplateVO.class);
        
        return ResultUtils.success(vo);
    }
    
    @PostMapping
    @Operation(summary = "Create template")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<AgentTemplateEntity> createAgentTemplate(@Valid @RequestBody AgentTemplateEntity template) {
        // Next sort index
        template.setSort(agentTemplateService.getNextAvailableSort());
        
        boolean saved = agentTemplateService.save(template);
        if (saved) {
            return ResultUtils.success(template);
        } else {
            return ResultUtils.error("Failed to create template");
        }
    }
    
    @PutMapping
    @Operation(summary = "Update template")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<AgentTemplateEntity> updateAgentTemplate(@Valid @RequestBody AgentTemplateEntity template) {
        boolean updated = agentTemplateService.updateById(template);
        if (updated) {
            return ResultUtils.success(template);
        } else {
            return ResultUtils.error("Failed to update template");
        }
    }
    
    @DeleteMapping("/{id}")
    @Operation(summary = "Delete template")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<String> deleteAgentTemplate(@PathVariable("id") String id) {
        // Read sort before delete for reorder
        AgentTemplateEntity template = agentTemplateService.getById(id);
        if (template == null) {
            return ResultUtils.error("Template not found");
        }
        
        Integer deletedSort = template.getSort();
        
        // Delete row
        boolean deleted = agentTemplateService.removeById(id);
        if (deleted) {
            // Compact sort values for remaining rows
            agentTemplateService.reorderTemplatesAfterDelete(deletedSort);
            return ResultUtils.success("Template deleted");
        } else {
            return ResultUtils.error("Failed to delete template");
        }
    }
    
    
    @PostMapping("/batch-remove")
    @Operation(summary = "Batch delete templates")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<String> batchRemoveAgentTemplates(@RequestBody List<String> ids) {
        boolean deleted = agentTemplateService.removeByIds(ids);
        if (deleted) {
            return ResultUtils.success("Batch delete completed");
        } else {
            return ResultUtils.error("Batch delete failed");
        }
    }
}