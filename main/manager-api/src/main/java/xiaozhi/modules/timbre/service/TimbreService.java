package xiaozhi.modules.timbre.service;

import java.util.List;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.model.dto.VoiceDTO;
import xiaozhi.modules.timbre.dto.TimbreDataDTO;
import xiaozhi.modules.timbre.dto.TimbrePageDTO;
import xiaozhi.modules.timbre.entity.TimbreEntity;
import xiaozhi.modules.timbre.vo.TimbreDetailsVO;

/**
 * Timbre service interface.
 *
 * @author zjy
 * @since 2025-3-21
 */
public interface TimbreService extends BaseService<TimbreEntity> {
    /**
     * Paginates timbres for the given TTS model.
     *
     * @param dto pagination parameters
     * @return paginated timbre list
     */
    PageData<TimbreDetailsVO> page(TimbrePageDTO dto);

    /**
     * Returns timbre details by ID.
     *
     * @param timbreId timbre ID
     * @return timbre details, or {@code null} if not found
     */
    TimbreDetailsVO get(String timbreId);

    /**
     * Saves a new timbre.
     *
     * @param dto data to persist
     */
    void save(TimbreDataDTO dto);

    /**
     * Updates an existing timbre.
     *
     * @param timbreId ID of the timbre to update
     * @param dto      updated fields
     */
    void update(String timbreId, TimbreDataDTO dto);

    /**
     * Deletes timbres by ID.
     *
     * @param ids timbre IDs to delete
     */
    void delete(String[] ids);

    List<VoiceDTO> getVoiceNames(String ttsModelId, String voiceName);

    /**
     * Resolves the display name for a timbre ID.
     *
     * @param id timbre ID
     * @return timbre name, or {@code null}
     */
    String getTimbreNameById(String id);

    /**
     * Looks up timbre information by voice code within a TTS model.
     *
     * @param ttsModelId TTS model ID
     * @param voiceCode  voice code ({@code tts_voice})
     * @return voice DTO, or {@code null}
     */
    VoiceDTO getByVoiceCode(String ttsModelId, String voiceCode);
}
