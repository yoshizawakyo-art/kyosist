/**
 * ═══════════════════════════════════════════════════════════════════════════
 * Login Form Module
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Handles user authentication by submitting email and password to the login
 * API endpoint. Stores JWT token in localStorage upon successful authentication.
 *
 * Features:
 * - Email and password validation
 * - Form submission and API integration
 * - JWT token storage and management
 * - Error handling and user feedback
 * - Loading state during authentication
 */

const LOGIN_API_ENDPOINT = "/api/auth/login";
const JWT_TOKEN_KEY = "kyosist_auth_token";
const LOGIN_FORM_ID = "login-form";
const LOGIN_BTN_ID = "login-btn";
const FORM_ERROR_ID = "form-error";

/**
 * Initializes the login form and attaches event listeners.
 * Called when the DOM is ready.
 */
function initializeLoginForm() {
  const form = document.getElementById(LOGIN_FORM_ID);
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");

  if (!form) {
    console.error("Login form not found");
    return;
  }

  form.addEventListener("submit", function handleFormSubmit(event) {
    event.preventDefault();
    handleLoginSubmit(emailInput, passwordInput);
  });

  emailInput.addEventListener("blur", function validateEmailField() {
    validateEmail(emailInput);
  });

  passwordInput.addEventListener("blur", function validatePasswordField() {
    validatePassword(passwordInput);
  });
}

/**
 * Validates email format according to HTML5 email specification.
 * Clears error message on valid input.
 *
 * @param {HTMLInputElement} emailInput - The email input element
 * @returns {boolean} True if email is valid, false otherwise
 */
function validateEmail(emailInput) {
  const errorElement = document.getElementById("email-error");
  const emailValue = emailInput.value.trim();

  if (!emailValue) {
    emailInput.classList.add("error");
    errorElement.textContent = "メールアドレスは必須です";
    return false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(emailValue)) {
    emailInput.classList.add("error");
    errorElement.textContent = "有効なメールアドレスを入力してください";
    return false;
  }

  emailInput.classList.remove("error");
  errorElement.textContent = "";
  return true;
}

/**
 * Validates password field for minimum length requirement.
 * Clears error message on valid input.
 *
 * @param {HTMLInputElement} passwordInput - The password input element
 * @returns {boolean} True if password is valid, false otherwise
 */
function validatePassword(passwordInput) {
  const errorElement = document.getElementById("password-error");
  const passwordValue = passwordInput.value;

  if (!passwordValue) {
    passwordInput.classList.add("error");
    errorElement.textContent = "パスワードは必須です";
    return false;
  }

  if (passwordValue.length < 6) {
    passwordInput.classList.add("error");
    errorElement.textContent = "パスワードは6文字以上である必要があります";
    return false;
  }

  passwordInput.classList.remove("error");
  errorElement.textContent = "";
  return true;
}

/**
 * Validates the entire form and returns all validation results.
 *
 * @param {HTMLInputElement} emailInput - The email input element
 * @param {HTMLInputElement} passwordInput - The password input element
 * @returns {boolean} True if all fields are valid, false otherwise
 */
function validateForm(emailInput, passwordInput) {
  const emailValid = validateEmail(emailInput);
  const passwordValid = validatePassword(passwordInput);
  return emailValid && passwordValid;
}

/**
 * Clears all field-level error messages from the form.
 */
function clearFieldErrors() {
  const emailError = document.getElementById("email-error");
  const passwordError = document.getElementById("password-error");

  emailError.textContent = "";
  passwordError.textContent = "";

  document.getElementById("email").classList.remove("error");
  document.getElementById("password").classList.remove("error");
}

/**
 * Displays a form-level error message to the user.
 *
 * @param {string} message - The error message to display
 */
function displayFormError(message) {
  const formErrorElement = document.getElementById(FORM_ERROR_ID);
  formErrorElement.textContent = message;
}

/**
 * Clears the form-level error message.
 */
function clearFormError() {
  const formErrorElement = document.getElementById(FORM_ERROR_ID);
  formErrorElement.textContent = "";
}

/**
 * Sets the loading state of the login button.
 *
 * @param {boolean} isLoading - True to show loading state, false to hide
 */
function setButtonLoading(isLoading) {
  const button = document.getElementById(LOGIN_BTN_ID);
  const btnText = button.querySelector(".btn-text");
  const btnLoader = button.querySelector(".btn-loader");

  button.disabled = isLoading;

  if (isLoading) {
    btnText.style.display = "none";
    btnLoader.style.display = "inline";
  } else {
    btnText.style.display = "inline";
    btnLoader.style.display = "none";
  }
}

/**
 * Calls the login API endpoint with the provided credentials.
 *
 * @param {string} email - The user's email address
 * @param {string} password - The user's password
 * @returns {Promise<{token: string}>} The login response with JWT token
 * @throws {Error} If the login request fails
 */
async function callLoginAPI(email, password) {
  const response = await fetch(LOGIN_API_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: email,
      password: password,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(function parseError() {
      return { detail: response.statusText };
    });
    const errorMessage = errorData.detail || "ログインに失敗しました";
    throw new Error(errorMessage);
  }

  return await response.json();
}

/**
 * Stores the JWT token in localStorage for future authenticated requests.
 *
 * @param {string} token - The JWT token to store
 */
function storeAuthToken(token) {
  localStorage.setItem(JWT_TOKEN_KEY, token);
}

/**
 * Retrieves the stored JWT token from localStorage.
 *
 * @returns {string|null} The stored JWT token or null if not found
 */
function getAuthToken() {
  return localStorage.getItem(JWT_TOKEN_KEY);
}

/**
 * Handles the login form submission: validates input, calls API,
 * stores token, and redirects on success.
 *
 * @param {HTMLInputElement} emailInput - The email input element
 * @param {HTMLInputElement} passwordInput - The password input element
 */
async function handleLoginSubmit(emailInput, passwordInput) {
  clearFormError();
  clearFieldErrors();

  if (!validateForm(emailInput, passwordInput)) {
    return;
  }

  setButtonLoading(true);

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  try {
    const loginResponse = await callLoginAPI(email, password);

    if (!loginResponse.token) {
      throw new Error("レスポンスにトークンが含まれていません");
    }

    storeAuthToken(loginResponse.token);
    window.location.href = "/";
  } catch (error) {
    const errorMessage = error.message || "予期しないエラーが発生しました";
    displayFormError(errorMessage);
    setButtonLoading(false);
  }
}

document.addEventListener("DOMContentLoaded", initializeLoginForm);
