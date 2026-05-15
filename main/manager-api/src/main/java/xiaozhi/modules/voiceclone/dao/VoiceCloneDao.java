package xiaozhi.modules.voiceclone.dao;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.model.dto.VoiceDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;

/**
 * Voice clone persistence.
 */
@Mapper
public interface VoiceCloneDao extends BaseMapper<VoiceCloneEntity> {
    /**
     * Voices that finished training successfully for the user and model.
     *
     * @param modelId model ID
     * @param userId  user ID
     * @return successfully trained voices
     */
    List<VoiceDTO> getTrainSuccess(String modelId, Long userId);

}
