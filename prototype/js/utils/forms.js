// Form validation and handling utilities

const Forms = {
    // Validate email format
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validate required fields
    validateRequired(value) {
        return value !== null && value !== undefined && String(value).trim() !== '';
    },

    // Validate minimum length
    validateMinLength(value, minLength) {
        return String(value).length >= minLength;
    },

    // Validate maximum length
    validateMaxLength(value, maxLength) {
        return String(value).length <= maxLength;
    },

    // Show error message
    showError(field, message) {
        const fieldElement = typeof field === 'string' ? document.getElementById(field) : field;
        if (!fieldElement) return;

        // Remove existing error
        this.clearError(fieldElement);

        // Add error class
        fieldElement.classList.add('error');
        
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        errorElement.id = `${fieldElement.id || 'field'}_error`;
        
        // Insert after field
        fieldElement.parentNode.insertBefore(errorElement, fieldElement.nextSibling);
    },

    // Clear error message
    clearError(field) {
        const fieldElement = typeof field === 'string' ? document.getElementById(field) : field;
        if (!fieldElement) return;

        fieldElement.classList.remove('error');
        const errorElement = fieldElement.parentNode.querySelector(`#${fieldElement.id || 'field'}_error`);
        if (errorElement) {
            errorElement.remove();
        }
    },

    // Validate form field
    validateField(field, rules) {
        const fieldElement = typeof field === 'string' ? document.getElementById(field) : field;
        if (!fieldElement) return false;

        const value = fieldElement.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (rules.required && !this.validateRequired(value)) {
            isValid = false;
            errorMessage = rules.requiredMessage || 'This field is required';
        }

        // Email validation
        if (isValid && rules.email && value && !this.validateEmail(value)) {
            isValid = false;
            errorMessage = rules.emailMessage || 'Please enter a valid email address';
        }

        // Min length validation
        if (isValid && rules.minLength && value && !this.validateMinLength(value, rules.minLength)) {
            isValid = false;
            errorMessage = rules.minLengthMessage || `Minimum length is ${rules.minLength} characters`;
        }

        // Max length validation
        if (isValid && rules.maxLength && value && !this.validateMaxLength(value, rules.maxLength)) {
            isValid = false;
            errorMessage = rules.maxLengthMessage || `Maximum length is ${rules.maxLength} characters`;
        }

        // Custom validation
        if (isValid && rules.custom && typeof rules.custom === 'function') {
            const customResult = rules.custom(value);
            if (customResult !== true) {
                isValid = false;
                errorMessage = typeof customResult === 'string' ? customResult : 'Invalid value';
            }
        }

        if (!isValid) {
            this.showError(fieldElement, errorMessage);
        } else {
            this.clearError(fieldElement);
        }

        return isValid;
    },

    // Validate entire form
    validateForm(formId, fieldRules) {
        const form = document.getElementById(formId);
        if (!form) return false;

        let isValid = true;
        const fields = Object.keys(fieldRules);

        fields.forEach(fieldId => {
            const fieldValid = this.validateField(fieldId, fieldRules[fieldId]);
            if (!fieldValid) {
                isValid = false;
            }
        });

        return isValid;
    },

    // Get form data as object
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};

        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Handle checkboxes
        form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            data[checkbox.name] = checkbox.checked;
        });

        return data;
    },

    // Set form data
    setFormData(formId, data) {
        const form = document.getElementById(formId);
        if (!form) return;

        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (!field) return;

            if (field.type === 'checkbox') {
                field.checked = Boolean(data[key]);
            } else if (field.type === 'radio') {
                const radio = form.querySelector(`[name="${key}"][value="${data[key]}"]`);
                if (radio) radio.checked = true;
            } else {
                field.value = data[key] || '';
            }
        });
    },

    // Reset form
    resetForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        form.reset();
        
        // Clear all errors
        form.querySelectorAll('.error').forEach(field => {
            field.classList.remove('error');
        });
        form.querySelectorAll('.error-message').forEach(error => {
            error.remove();
        });
    },

    // Character counter
    setupCharCounter(textareaId, counterId, maxLength = null) {
        const textarea = document.getElementById(textareaId);
        const counter = document.getElementById(counterId);
        
        if (!textarea || !counter) return;

        const updateCounter = () => {
            const length = textarea.value.length;
            counter.textContent = length;
            
            if (maxLength) {
                const percentage = (length / maxLength) * 100;
                if (percentage > 90) {
                    counter.style.color = 'var(--error-red)';
                } else if (percentage > 75) {
                    counter.style.color = 'var(--warning-yellow)';
                } else {
                    counter.style.color = 'var(--medium-gray)';
                }
            }
        };

        textarea.addEventListener('input', updateCounter);
        updateCounter(); // Initial count
    }
};

// Make available globally
if (typeof window !== 'undefined') {
    window.Forms = Forms;
}

