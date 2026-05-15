package xiaozhi.modules.sys.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import xiaozhi.modules.sys.entity.SysUserEntity;

public interface SysUserRepository extends JpaRepository<SysUserEntity, Long>, JpaSpecificationExecutor<SysUserEntity> {

    Optional<SysUserEntity> findFirstByUsernameOrderByIdAsc(String username);
}
