package xiaozhi.modules.sys.vo;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Lightweight dictionary entry for API responses.
 */
@Data
@NoArgsConstructor
@Schema(description = "Dictionary entry")
public class SysDictDataItem implements Serializable {

    /** JPQL {@code SELECT NEW ... (label, value)} */
    public SysDictDataItem(String name, String key) {
        this.name = name;
        this.key = key;
    }

    @Schema(description = "Display label")
    private String name;

    @Schema(description = "Stored value")
    private String key;
}
