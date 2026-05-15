package xiaozhi.modules.agent.service.impl;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;
import java.util.concurrent.Executor;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.dao.AgentVoicePrintDao;
import xiaozhi.modules.agent.dto.AgentVoicePrintSaveDTO;
import xiaozhi.modules.agent.dto.AgentVoicePrintUpdateDTO;
import xiaozhi.modules.agent.dto.IdentifyVoicePrintResponse;
import xiaozhi.modules.agent.entity.AgentVoicePrintEntity;
import xiaozhi.modules.agent.service.AgentChatAudioService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentVoicePrintService;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * {@link AgentVoicePrintService} implementation.
 *
 * @author zjy
 */
@Service
@Slf4j
public class AgentVoicePrintServiceImpl extends ServiceImpl<AgentVoicePrintDao, AgentVoicePrintEntity>
        implements AgentVoicePrintService {
    private final AgentChatAudioService agentChatAudioService;
    private final RestTemplate restTemplate;
    private final SysParamsService sysParamsService;
    private final AgentChatHistoryService agentChatHistoryService;
    private final TransactionTemplate transactionTemplate;
    private final Double RECOGNITION = 0.45;
    private final Executor taskExecutor;

    public AgentVoicePrintServiceImpl(AgentChatAudioService agentChatAudioService, RestTemplate restTemplate,
                                      SysParamsService sysParamsService, AgentChatHistoryService agentChatHistoryService,
                                      TransactionTemplate transactionTemplate, @Qualifier("taskExecutor") Executor taskExecutor) {
        this.agentChatAudioService = agentChatAudioService;
        this.restTemplate = restTemplate;
        this.sysParamsService = sysParamsService;
        this.agentChatHistoryService = agentChatHistoryService;
        this.transactionTemplate = transactionTemplate;
        this.taskExecutor = taskExecutor;
    }

    @Override
    public boolean insert(AgentVoicePrintSaveDTO dto) {
        if (Boolean.TRUE.equals(dto.getDirectRegistered()) && StringUtils.isNotBlank(dto.getSpeakerId())) {
            AgentVoicePrintEntity entity = ConvertUtils.sourceToTarget(dto, AgentVoicePrintEntity.class);
            entity.setId(dto.getSpeakerId());
            return Boolean.TRUE.equals(transactionTemplate.execute(status -> {
                try {
                    int row = baseMapper.insert(entity);
                    if (row != 1) {
                        status.setRollbackOnly();
                        return false;
                    }
                    return true;
                } catch (Exception e) {
                    status.setRollbackOnly();
                    log.error("Voice print save failed (direct): {}", e.getMessage());
                    throw new RenException(ErrorCode.VOICE_PRINT_SAVE_ERROR);
                }
            }));
        }

        ByteArrayResource resource = getVoicePrintAudioWAV(dto.getAgentId(), dto.getAudioId());
        IdentifyVoicePrintResponse response = identifyVoicePrint(dto.getAgentId(), resource);
        if (response != null && response.getScore() > RECOGNITION) {
            AgentVoicePrintEntity existingVoicePrint = baseMapper.selectById(response.getSpeakerId());
            String existingUserName = existingVoicePrint != null ? existingVoicePrint.getSourceName() : "Unknown user";
            throw new RenException(ErrorCode.VOICEPRINT_ALREADY_REGISTERED, existingUserName);
        }
        AgentVoicePrintEntity entity = ConvertUtils.sourceToTarget(dto, AgentVoicePrintEntity.class);
        return Boolean.TRUE.equals(transactionTemplate.execute(status -> {
            try {
                int row = baseMapper.insert(entity);
                if (row != 1) {
                    status.setRollbackOnly();
                    return false;
                }
                registerVoicePrint(entity.getId(), resource);
                return true;
            } catch (RenException e) {
                status.setRollbackOnly();
                throw e;
            } catch (Exception e) {
                status.setRollbackOnly();
                log.error("Voice print save failed: {}", e.getMessage());
                throw new RenException(ErrorCode.VOICE_PRINT_SAVE_ERROR);
            }
        }));
    }

    @Override
    public boolean delete(Long userId, String voicePrintId) {
        boolean b = Boolean.TRUE.equals(transactionTemplate.execute(status -> {
            try {
                int row = baseMapper.delete(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                        .eq(AgentVoicePrintEntity::getId, voicePrintId)
                        .eq(AgentVoicePrintEntity::getCreator, userId));
                if (row != 1) {
                    status.setRollbackOnly();
                    return false;
                }

                return true;
            } catch (Exception e) {
                status.setRollbackOnly();
                log.error("Voice print delete failed: {}", e.getMessage());
                throw new RenException(ErrorCode.VOICEPRINT_DELETE_ERROR);
            }
        }));
        if(b){
            taskExecutor.execute(()-> {
                try {
                    cancelVoicePrint(voicePrintId);
                }catch (RuntimeException e) {
                    log.error("Voice print remote delete failed: {}, id={}", e.getMessage(),voicePrintId);
                }
            });
        }
        return b;
    }

    @Override
    public List<AgentVoicePrintVO> list(Long userId, String agentId) {
        List<AgentVoicePrintEntity> list = baseMapper.selectList(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                .eq(AgentVoicePrintEntity::getAgentId, agentId)
                .eq(AgentVoicePrintEntity::getCreator, userId));
        return list.stream().map(entity -> {
            return ConvertUtils.sourceToTarget(entity, AgentVoicePrintVO.class);
        }).toList();

    }

    @Override
    public boolean update(Long userId, AgentVoicePrintUpdateDTO dto) {
        AgentVoicePrintEntity agentVoicePrintEntity = baseMapper
                .selectOne(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                        .eq(AgentVoicePrintEntity::getId, dto.getId())
                        .eq(AgentVoicePrintEntity::getCreator, userId));
        if (agentVoicePrintEntity == null) {
            return false;
        }
        String audioId = dto.getAudioId();
        String agentId = agentVoicePrintEntity.getAgentId();
        ByteArrayResource resource;
        if (!StringUtils.isEmpty(audioId) && !audioId.equals(agentVoicePrintEntity.getAudioId())) {
            resource = getVoicePrintAudioWAV(agentId, audioId);

            IdentifyVoicePrintResponse response = identifyVoicePrint(agentId, resource);
            if (response != null && response.getScore() > RECOGNITION) {
                if (!response.getSpeakerId().equals(dto.getId())) {
                    AgentVoicePrintEntity existingVoicePrint = baseMapper.selectById(response.getSpeakerId());
                    String existingUserName = existingVoicePrint != null ? existingVoicePrint.getSourceName() : "Unknown user";
                    throw new RenException(ErrorCode.VOICEPRINT_UPDATE_NOT_ALLOWED, existingUserName);
                }
            }
        } else {
            resource = null;
        }
        return Boolean.TRUE.equals(transactionTemplate.execute(status -> {
            try {
                AgentVoicePrintEntity entity = ConvertUtils.sourceToTarget(dto, AgentVoicePrintEntity.class);
                int row = baseMapper.updateById(entity);
                if (row != 1) {
                    status.setRollbackOnly();
                    return false;
                }
                if (resource != null) {
                    String id = entity.getId();
                    cancelVoicePrint(id);
                    registerVoicePrint(id, resource);
                }
                return true;
            } catch (RenException e) {
                status.setRollbackOnly();
                throw e;
            } catch (Exception e) {
                status.setRollbackOnly();
                log.error("Voice print update failed: {}", e.getMessage());
                throw new RenException(ErrorCode.VOICEPRINT_UPDATE_ADMIN_ERROR);
            }
        }));
    }

    private URI getVoicePrintURI() {
        String voicePrint = sysParamsService.getValue(Constant.SERVER_VOICE_PRINT, true);
        try {
            return new URI(voicePrint);
        } catch (URISyntaxException e) {
            log.error("Invalid voice-print API URL: {}, error: {}", voicePrint, e.getMessage());
                throw new RenException(ErrorCode.VOICEPRINT_API_URI_ERROR);
        }
    }

    private String getBaseUrl(URI uri) {
        String protocol = uri.getScheme();
        String host = uri.getHost();
        int port = uri.getPort();
        if (port == -1) {
            return "%s://%s".formatted(protocol, host);
        } else {
            return "%s://%s:%s".formatted(protocol, host, port);
        }
    }

    private String getAuthorization(URI uri) {
        String query = uri.getQuery();
        String str = "key=";
        return "Bearer " + query.substring(query.indexOf(str) + str.length());
    }

    private ByteArrayResource getVoicePrintAudioWAV(String agentId, String audioId) {
        boolean b = agentChatHistoryService.isAudioOwnedByAgent(audioId, agentId);
        if (!b) {
            throw new RenException(ErrorCode.VOICEPRINT_AUDIO_NOT_BELONG_AGENT);
        }
        byte[] audio = agentChatAudioService.getAudio(audioId);
        if (audio == null || audio.length == 0) {
            throw new RenException(ErrorCode.VOICEPRINT_AUDIO_EMPTY);
        }
        return new ByteArrayResource(audio) {
            @Override
            public String getFilename() {
                return "VoicePrint.WAV";
            }
        };
    }

    private void registerVoicePrint(String id, ByteArrayResource resource) {
        URI uri = getVoicePrintURI();
        String baseUrl = getBaseUrl(uri);
        String requestUrl = baseUrl + "/voiceprint/register";
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("speaker_id", id);
        body.add("file", resource);

        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", getAuthorization(uri));
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        ResponseEntity<String> response = restTemplate.postForEntity(requestUrl, requestEntity, String.class);

        if (response.getStatusCode() != HttpStatus.OK) {
            log.error("Voice print register HTTP failed, url={}", requestUrl);
            throw new RenException(ErrorCode.VOICEPRINT_REGISTER_REQUEST_ERROR);
        }
        String responseBody = response.getBody();
        if (responseBody == null || !responseBody.contains("true")) {
            log.error("Voice print register rejected, body={}", responseBody == null ? "(empty)" : responseBody);
            throw new RenException(ErrorCode.VOICEPRINT_REGISTER_PROCESS_ERROR);
        }
    }

    private void cancelVoicePrint(String voicePrintId) {
        URI uri = getVoicePrintURI();
        String baseUrl = getBaseUrl(uri);
        String requestUrl = baseUrl + "/voiceprint/" + voicePrintId;
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", getAuthorization(uri));
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(headers);

        ResponseEntity<String> response = restTemplate.exchange(requestUrl, HttpMethod.DELETE, requestEntity,
                String.class);
        if (response.getStatusCode() != HttpStatus.OK) {
            log.error("Voice print unregister HTTP failed, url={}", requestUrl);
            throw new RenException(ErrorCode.VOICEPRINT_UNREGISTER_REQUEST_ERROR);
        }
        String responseBody = response.getBody();
        if (responseBody == null || !responseBody.contains("true")) {
            log.error("Voice print unregister rejected, body={}", responseBody == null ? "(empty)" : responseBody);
            throw new RenException(ErrorCode.VOICEPRINT_UNREGISTER_PROCESS_ERROR);
        }
    }

    private IdentifyVoicePrintResponse identifyVoicePrint(String agentId, ByteArrayResource resource) {

        List<AgentVoicePrintEntity> agentVoicePrintList = baseMapper
                .selectList(new LambdaQueryWrapper<AgentVoicePrintEntity>()
                        .select(AgentVoicePrintEntity::getId)
                        .eq(AgentVoicePrintEntity::getAgentId, agentId));

        if (agentVoicePrintList.isEmpty()) {
            return null;
        }
        URI uri = getVoicePrintURI();
        String baseUrl = getBaseUrl(uri);
        String requestUrl = baseUrl + "/voiceprint/identify";
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

        String speakerIds = agentVoicePrintList.stream()
                .map(AgentVoicePrintEntity::getId)
                .collect(Collectors.joining(","));
        body.add("speaker_ids", speakerIds);
        body.add("file", resource);

        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", getAuthorization(uri));
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        ResponseEntity<String> response = restTemplate.postForEntity(requestUrl, requestEntity, String.class);

        if (response.getStatusCode() != HttpStatus.OK) {
            log.error("Voice print identify HTTP failed, url={}", requestUrl);
            throw new RenException(ErrorCode.VOICEPRINT_IDENTIFY_REQUEST_ERROR);
        }
        String responseBody = response.getBody();
        if (responseBody != null) {
            return JsonUtils.parseObject(responseBody, IdentifyVoicePrintResponse.class);
        }
        return null;
    }
}
