package xiaozhi.modules.device.dao;

import java.util.Date;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.device.entity.DeviceEntity;

@Mapper
public interface DeviceDao extends BaseMapper<DeviceEntity> {
    /**
     * Latest {@code last_connected_at} among devices bound to an agent.
     *
     * @param agentId agent id
     * @return max timestamp or null
     */
    Date getAllLastConnectedAtByAgentId(String agentId);

}