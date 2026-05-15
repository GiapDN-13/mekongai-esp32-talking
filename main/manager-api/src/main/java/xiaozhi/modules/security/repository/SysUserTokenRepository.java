package xiaozhi.modules.security.repository;

import java.util.Date;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import xiaozhi.modules.security.entity.SysUserTokenEntity;

public interface SysUserTokenRepository extends JpaRepository<SysUserTokenEntity, Long> {

    Optional<SysUserTokenEntity> findByToken(String token);

    Optional<SysUserTokenEntity> findFirstByUserIdOrderByIdAsc(Long userId);

    @Modifying(clearAutomatically = true)
    @Query("UPDATE SysUserTokenEntity t SET t.expireDate = :expireDate WHERE t.userId = :userId")
    int logout(@Param("userId") Long userId, @Param("expireDate") Date expireDate);
}
