package xiaozhi.common.validator;

import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

import org.hibernate.validator.messageinterpolation.ResourceBundleMessageInterpolator;
import org.springframework.context.i18n.LocaleContextHolder;
import org.springframework.context.support.ResourceBundleMessageSource;
import org.springframework.validation.beanvalidation.MessageSourceResourceBundleLocator;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import xiaozhi.common.exception.RenException;

/**
 * Hibernate Validator helpers.
 * @see <a href="http://docs.jboss.org/hibernate/validator/6.0/reference/en-US/html_single/">Hibernate Validator reference</a>
 */
public class ValidatorUtils {

    private static ResourceBundleMessageSource getMessageSource() {
        ResourceBundleMessageSource bundleMessageSource = new ResourceBundleMessageSource();
        bundleMessageSource.setDefaultEncoding("UTF-8");
        bundleMessageSource.setBasenames("i18n/validation");
        return bundleMessageSource;
    }

    /**
     * Validate a bean; throws {@link RenException} on first constraint violation.
     *
     * @param object entity to validate
     * @param groups validation groups
     */
    public static void validateEntity(Object object, Class<?>... groups)
            throws RenException {
        Locale.setDefault(LocaleContextHolder.getLocale());
        Validator validator = Validation.byDefaultProvider().configure().messageInterpolator(
                new ResourceBundleMessageInterpolator(new MessageSourceResourceBundleLocator(getMessageSource())))
                .buildValidatorFactory().getValidator();

        Set<ConstraintViolation<Object>> constraintViolations = validator.validate(object, groups);
        if (!constraintViolations.isEmpty()) {
            ConstraintViolation<Object> constraint = constraintViolations.iterator().next();
            throw new RenException(constraint.getMessage());
        }
    }

    /**
     * E.164-style international phone pattern (leading +, country code, subscriber number).
     * Examples: +8613800138000, +12345678900, +447123456789
     */
    private static final String INTERNATIONAL_PHONE_REGEX = "^\\+[1-9]\\d{0,3}[1-9]\\d{4,14}$";

    /**
     * Whether {@code phone} matches {@link #INTERNATIONAL_PHONE_REGEX}.
     *
     * @param phone phone number including country code (e.g. +8613800138000)
     * @return true if valid
     */
    public static boolean isValidPhone(String phone) {
        if (phone == null || phone.isEmpty()) {
            return false;
        }

        // Require international format with leading +
        Pattern pattern = Pattern.compile(INTERNATIONAL_PHONE_REGEX);
        return pattern.matcher(phone).matches();
    }
}