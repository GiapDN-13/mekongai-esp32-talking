package xiaozhi.modules.voiceclone.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.voiceclone.dto.VoiceCloneDTO;
import xiaozhi.modules.voiceclone.dto.VoiceCloneResponseDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;

/**
 * Voice clone management.
 */
public interface VoiceCloneService extends BaseService<VoiceCloneEntity> {

    /**
     * Paginated query.
     */
    PageData<VoiceCloneEntity> page(Map<String, Object> params);

    /**
     * Save voice clone records.
     */
    void save(VoiceCloneDTO dto);

    /**
     * Batch delete.
     */
    void delete(String[] ids);

    /**
     * List voice clones for a user.
     *
     * @param userId user ID
     * @return voice clone list
     */
    List<VoiceCloneEntity> getByUserId(Long userId);

    /**
     * Paginated query with model name and user name populated.
     */
    PageData<VoiceCloneResponseDTO> pageWithNames(Map<String, Object> params);

    /**
     * Get by ID with model name and user name populated.
     */
    VoiceCloneResponseDTO getByIdWithNames(String id);

    /**
     * List by user ID with model name and user name populated.
     */
    List<VoiceCloneResponseDTO> getByUserIdWithNames(Long userId);

    /**
     * Upload audio file.
     */
    void uploadVoice(String id, MultipartFile voiceFile) throws Exception;

    /**
     * Update voice clone display name.
     */
    void updateName(String id, String name);

    /**
     * Get raw audio bytes.
     */
    byte[] getVoiceData(String id);

    /**
     * Run voice cloning training (e.g. Volcano Engine).
     *
     * @param cloneId voice clone record ID
     */
    void cloneAudio(String cloneId);
}
