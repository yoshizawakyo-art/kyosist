/**
 * Kyosist サインアップフォーム
 * メールアドレスとパスワードで新規登録し、JWTトークンをlocalStorageに保存する
 */

const API_BASE_URL = '/api';
const STORAGE_TOKEN_KEY = 'kyosist_token';
const STORAGE_USER_KEY = 'kyosist_user';

const signupForm = document.getElementById('signupForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const submitButton = document.getElementById('submitButton');
const spinner = document.getElementById('spinner');
const emailError = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');
const apiError = document.getElementById('apiError');

/**
 * メールアドレスのバリデーション
 * @param {string} email - バリデーション対象のメールアドレス
 * @returns {boolean} 有効な場合true
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * パスワードのバリデーション
 * @param {string} password - バリデーション対象のパスワード
 * @returns {boolean} 有効な場合true（8文字以上）
 */
function validatePassword(password) {
    return password.length >= 8;
}

/**
 * フォームバリデーション実行
 * @returns {boolean} すべてのフィールドが有効な場合true
 */
function validateForm() {
    let isValid = true;

    // メールアドレスのバリデーション
    if (!emailInput.value.trim()) {
        emailError.textContent = 'メールアドレスを入力してください';
        emailInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    } else if (!validateEmail(emailInput.value)) {
        emailError.textContent = '有効なメールアドレスを入力してください';
        emailInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    } else {
        emailError.textContent = '';
        emailInput.setAttribute('aria-invalid', 'false');
    }

    // パスワードのバリデーション
    if (!passwordInput.value) {
        passwordError.textContent = 'パスワードを入力してください';
        passwordInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    } else if (!validatePassword(passwordInput.value)) {
        passwordError.textContent = 'パスワードは8文字以上である必要があります';
        passwordInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    } else {
        passwordError.textContent = '';
        passwordInput.setAttribute('aria-invalid', 'false');
    }

    return isValid;
}

/**
 * ローディング状態を表示する
 */
function setLoading(isLoading) {
    if (isLoading) {
        submitButton.disabled = true;
        submitButton.classList.add('is-loading');
        spinner.style.display = 'inline-block';
    } else {
        submitButton.disabled = false;
        submitButton.classList.remove('is-loading');
        spinner.style.display = 'none';
    }
}

/**
 * APIエラーを表示する
 * @param {string} message - エラーメッセージ
 */
function showApiError(message) {
    apiError.textContent = message;
    apiError.style.display = 'block';
    apiError.classList.remove('success');
}

/**
 * APIエラーをクリアする
 */
function clearApiError() {
    apiError.textContent = '';
    apiError.style.display = 'none';
}

/**
 * フォームをクリアする
 */
function clearForm() {
    signupForm.reset();
    emailError.textContent = '';
    passwordError.textContent = '';
}

/**
 * サインアップ処理実行
 * @param {string} email - メールアドレス
 * @param {string} password - パスワード
 */
async function performSignup(email, password) {
    setLoading(true);
    clearApiError();

    try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            // 409: メール重複
            if (response.status === 409) {
                showApiError('このメールアドレスは既に登録されています');
            } else {
                const errorMessage = data.detail || '登録に失敗しました';
                showApiError(`登録に失敗しました: ${errorMessage}`);
            }
            setLoading(false);
            return;
        }

        // トークンとユーザー情報をlocalStorageに保存
        if (data.token) {
            localStorage.setItem(STORAGE_TOKEN_KEY, data.token);
        }

        if (data.user) {
            localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(data.user));
        }

        // フォームをクリア
        clearForm();

        // 登録成功メッセージを表示して、ダッシュボードにリダイレクト
        showApiSuccess('登録に成功しました');

        setTimeout(function() {
            window.location.href = '/chat/index.html';
        }, 1000);

    } catch (error) {
        console.error('サインアップエラー:', error);
        showApiError('ネットワークエラーが発生しました。もう一度お試しください。');
        setLoading(false);
    }
}

/**
 * サインアップ成功メッセージを表示する
 * @param {string} message - 成功メッセージ
 */
function showApiSuccess(message) {
    apiError.textContent = message;
    apiError.classList.add('success');
    apiError.style.display = 'block';
}

/**
 * フォーム送信ハンドラ
 * @param {Event} event - フォーム送信イベント
 */
function handleSubmit(event) {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    performSignup(email, password);
}

/**
 * リアルタイムバリデーション - メールアドレス
 */
function handleEmailBlur() {
    const email = emailInput.value.trim();
    if (email && !validateEmail(email)) {
        emailError.textContent = '有効なメールアドレスを入力してください';
        emailInput.setAttribute('aria-invalid', 'true');
    } else {
        emailError.textContent = '';
        emailInput.setAttribute('aria-invalid', 'false');
    }
}

/**
 * リアルタイムバリデーション - パスワード
 */
function handlePasswordBlur() {
    const password = passwordInput.value;
    if (password && !validatePassword(password)) {
        passwordError.textContent = 'パスワードは8文字以上である必要があります';
        passwordInput.setAttribute('aria-invalid', 'true');
    } else {
        passwordError.textContent = '';
        passwordInput.setAttribute('aria-invalid', 'false');
    }
}

/**
 * 初期化処理
 */
function init() {
    // フォーム送信イベントをリッスン
    signupForm.addEventListener('submit', handleSubmit);

    // リアルタイムバリデーション
    emailInput.addEventListener('blur', handleEmailBlur);
    passwordInput.addEventListener('blur', handlePasswordBlur);

    // 既にログインしている場合はダッシュボードにリダイレクト
    const existingToken = localStorage.getItem(STORAGE_TOKEN_KEY);
    if (existingToken) {
        window.location.href = '/chat/index.html';
    }
}

// DOMContentLoaded時に初期化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
