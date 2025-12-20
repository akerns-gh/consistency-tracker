/**
 * Login Form Test Script
 * 
 * Instructions:
 * 1. Navigate to http://localhost:5173/login
 * 2. Open browser DevTools (F12)
 * 3. Go to Console tab
 * 4. Copy and paste this entire script
 * 5. Press Enter to run
 * 
 * The script will test all validation scenarios and report results
 */

(function() {
    console.log('%c=== Login Form Automated Test Suite ===', 'font-size: 18px; font-weight: bold; color: #96c855; padding: 10px;');
    console.log('Starting tests...\n');
    
    const results = {
        passed: 0,
        failed: 0,
        tests: []
    };
    
    function logTest(name, passed, details = '') {
        results.tests.push({ name, passed, details });
        if (passed) {
            results.passed++;
            console.log(`✅ ${name}`, details ? `- ${details}` : '');
        } else {
            results.failed++;
            console.log(`❌ ${name}`, details ? `- ${details}` : '');
        }
    }
    
    function getFormElements() {
        return {
            email: document.getElementById('email'),
            password: document.getElementById('password'),
            submitButton: document.querySelector('form button[type="submit"]'),
            errorDiv: document.querySelector('.bg-red-50')
        };
    }
    
    function clearForm() {
        const { email, password } = getFormElements();
        if (email) email.value = '';
        if (password) password.value = '';
        // Clear any error messages
        const errorDiv = document.querySelector('.bg-red-50');
        if (errorDiv) errorDiv.remove();
    }
    
    function waitForError(timeout = 1000) {
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                const errorDiv = document.querySelector('.bg-red-50');
                if (errorDiv) {
                    clearInterval(checkInterval);
                    resolve(errorDiv.textContent.trim());
                }
            }, 100);
            
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve(null);
            }, timeout);
        });
    }
    
    async function testEmailValidation() {
        console.log('\n%c--- Email Validation Tests ---', 'font-size: 14px; font-weight: bold; color: #333;');
        
        const { email, password, submitButton } = getFormElements();
        
        if (!email || !password || !submitButton) {
            logTest('Form elements exist', false, 'Email, password, or submit button not found');
            return;
        }
        logTest('Form elements exist', true);
        
        // Test 1: Empty email
        clearForm();
        email.value = '';
        password.value = 'testpassword123';
        submitButton.click();
        const error1 = await waitForError();
        logTest('Empty email validation', 
            error1 && error1.includes('email address'), 
            `Got: "${error1}"`);
        
        // Test 2: Invalid email formats
        const invalidEmails = [
            { email: 'invalid-email', desc: 'No @ symbol' },
            { email: 'invalid@email', desc: 'No domain extension' },
            { email: '@email.com', desc: 'No local part' },
            { email: 'email@.com', desc: 'No domain' }
        ];
        
        for (const testCase of invalidEmails) {
            clearForm();
            email.value = testCase.email;
            password.value = 'testpassword123';
            submitButton.click();
            const error = await waitForError();
            logTest(`Invalid email: ${testCase.desc}`, 
                error && error.includes('valid email'), 
                `Email: "${testCase.email}", Got: "${error}"`);
        }
        
        // Test 3: Valid email formats
        const validEmails = [
            'test@example.com',
            'user.name@example.co.uk',
            'user+tag@example.com'
        ];
        
        for (const validEmail of validEmails) {
            clearForm();
            email.value = validEmail;
            password.value = 'testpassword123';
            submitButton.click();
            const error = await waitForError(500);
            // Valid email should pass client-side validation (may fail on server, but that's OK)
            logTest(`Valid email: ${validEmail}`, 
                !error || !error.includes('valid email'), 
                `Should pass client validation`);
        }
        
        // Test 4: Email trimming
        clearForm();
        email.value = '  test@example.com  ';
        password.value = 'testpassword123';
        submitButton.click();
        const error4 = await waitForError(500);
        logTest('Email trimming', 
            !error4 || !error4.includes('valid email'), 
            'Email should be trimmed before validation');
    }
    
    async function testPasswordValidation() {
        console.log('\n%c--- Password Validation Tests ---', 'font-size: 14px; font-weight: bold; color: #333;');
        
        const { email, password, submitButton } = getFormElements();
        
        // Test 1: Empty password
        clearForm();
        email.value = 'test@example.com';
        password.value = '';
        submitButton.click();
        const error1 = await waitForError();
        logTest('Empty password validation', 
            error1 && error1.includes('password'), 
            `Got: "${error1}"`);
    }
    
    async function testPasswordResetFlow() {
        console.log('\n%c--- Password Reset Flow Tests ---', 'font-size: 14px; font-weight: bold; color: #333;');
        
        // Check if "Forgot password" link exists
        const forgotLink = document.querySelector('a[href="#"]');
        if (!forgotLink || !forgotLink.textContent.includes('Forgot')) {
            logTest('Forgot password link exists', false);
            return;
        }
        logTest('Forgot password link exists', true);
        
        // Click forgot password link
        forgotLink.click();
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Check if reset form appeared
        const resetEmail = document.getElementById('resetEmail');
        if (!resetEmail) {
            logTest('Password reset form appears', false);
            return;
        }
        logTest('Password reset form appears', true);
        
        // Test empty reset email
        const resetSubmit = document.querySelector('form button[type="submit"]');
        if (resetSubmit) {
            resetEmail.value = '';
            resetSubmit.click();
            const error = await waitForError();
            logTest('Reset form - empty email validation', 
                error && error.includes('email'), 
                `Got: "${error}"`);
        }
        
        // Test invalid reset email format
        if (resetSubmit) {
            resetEmail.value = 'invalid-email';
            resetSubmit.click();
            const error = await waitForError();
            logTest('Reset form - invalid email format', 
                error && error.includes('valid email'), 
                `Got: "${error}"`);
        }
    }
    
    async function testPasswordRequirements() {
        console.log('\n%c--- Password Requirements Tests ---', 'font-size: 14px; font-weight: bold; color: #333;');
        console.log('Note: These tests require password change or reset form to be visible');
        
        // Check if password change form is visible
        const newPasswordInput = document.getElementById('newPassword');
        const confirmPasswordInput = document.getElementById('confirmPassword');
        
        if (!newPasswordInput || !confirmPasswordInput) {
            console.log('⚠️  Password change/reset form not visible. Skipping password requirement tests.');
            console.log('   (These will be tested when form is triggered)');
            return;
        }
        
        const submitButton = document.querySelector('form button[type="submit"]');
        
        // Test password mismatch
        newPasswordInput.value = 'Password123';
        confirmPasswordInput.value = 'Password456';
        submitButton.click();
        const error1 = await waitForError();
        logTest('Password mismatch validation', 
            error1 && error1.includes('match'), 
            `Got: "${error1}"`);
        
        // Test minimum length
        newPasswordInput.value = 'Short1';
        confirmPasswordInput.value = 'Short1';
        submitButton.click();
        const error2 = await waitForError();
        logTest('Password minimum length (12 chars)', 
            error2 && error2.includes('12'), 
            `Got: "${error2}"`);
        
        // Test missing lowercase
        newPasswordInput.value = 'PASSWORD123';
        confirmPasswordInput.value = 'PASSWORD123';
        submitButton.click();
        const error3 = await waitForError();
        logTest('Password requires lowercase letter', 
            error3 && error3.includes('lowercase'), 
            `Got: "${error3}"`);
        
        // Test missing uppercase
        newPasswordInput.value = 'password123';
        confirmPasswordInput.value = 'password123';
        submitButton.click();
        const error4 = await waitForError();
        logTest('Password requires uppercase letter', 
            error4 && error4.includes('uppercase'), 
            `Got: "${error4}"`);
        
        // Test missing number
        newPasswordInput.value = 'PasswordTest';
        confirmPasswordInput.value = 'PasswordTest';
        submitButton.click();
        const error5 = await waitForError();
        logTest('Password requires number', 
            error5 && error5.includes('number'), 
            `Got: "${error5}"`);
        
        // Test valid password
        newPasswordInput.value = 'Password123';
        confirmPasswordInput.value = 'Password123';
        submitButton.click();
        const error6 = await waitForError(500);
        logTest('Valid password format', 
            !error6 || (!error6.includes('12') && !error6.includes('lowercase') && 
                       !error6.includes('uppercase') && !error6.includes('number') && 
                       !error6.includes('match')), 
            'Should pass all requirements');
    }
    
    function testFormAccessibility() {
        console.log('\n%c--- Form Accessibility Tests ---', 'font-size: 14px; font-weight: bold; color: #333;');
        
        const email = document.getElementById('email');
        const password = document.getElementById('password');
        
        if (email) {
            logTest('Email field has type="email"', email.type === 'email');
            logTest('Email field has autocomplete', email.autocomplete === 'email');
            logTest('Email field is required', email.hasAttribute('required'));
        }
        
        if (password) {
            logTest('Password field has type="password"', password.type === 'password');
            logTest('Password field has autocomplete', password.autocomplete === 'current-password');
            logTest('Password field is required', password.hasAttribute('required'));
        }
    }
    
    // Run all tests
    async function runAllTests() {
        await testEmailValidation();
        await testPasswordValidation();
        testFormAccessibility();
        await testPasswordResetFlow();
        await testPasswordRequirements();
        
        // Print summary
        console.log('\n%c=== Test Summary ===', 'font-size: 16px; font-weight: bold; color: #96c855;');
        console.log(`✅ Passed: ${results.passed}`);
        console.log(`❌ Failed: ${results.failed}`);
        console.log(`📊 Total: ${results.passed + results.failed}`);
        console.log(`\nSuccess Rate: ${((results.passed / (results.passed + results.failed)) * 100).toFixed(1)}%`);
        
        if (results.failed > 0) {
            console.log('\n%cFailed Tests:', 'font-weight: bold; color: #f44336;');
            results.tests.filter(t => !t.passed).forEach(test => {
                console.log(`  ❌ ${test.name}`, test.details ? `- ${test.details}` : '');
            });
        }
        
        return results;
    }
    
    // Auto-run tests
    return runAllTests();
})();

