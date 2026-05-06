/**
 * Kyosist パスワードリセット実行フォーム
 * URLパラメータの token を使い、新しいパスワードを設定する。
 * 成功時はログイン画面へ自動遷移する。
 */

const API_BASE_URL = '/api';

const resetPasswordForm = document.getElementById('resetPasswordForm');
const passwordInput = document.getElementById('password');
const submitButton = document.getElementById('submitButton');
const spinner = document.getElementById('spinner');
const passwordError = document.getElementById('passwordError');
const apiError = document.getElementById('apiError');

const urlParams = new URLSearchParams(window.location.search);
const resetToken = urlParams.get('token');

/**
 * パスワードのバリデーション
 * @param {string} password - バリデーション対象のパスワード
 * @returns {boolean} 8文字以上の場合true
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
 * @param {boolean} isLoading - ローディング中かどうか
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
    apiError.classList.remove('success');
    apiError.style.display = 'block';
}

/**
 * APIメッセージ表示をクリアする
 */
function clearApiMessage() {
    apiError.textContent = '';
    apiError.classList.remove('success');
    apiError.style.display = 'none';
}

/**
 * 成功メッセージを表示する
 * @param {string} message - 成功メッセージ
 */
function showApiSuccess(message) {
    apiError.textContent = message;
    apiError.classList.add('success');
    apiError.style.display = 'block';
}

/**
 * パスワードリセット成功時のリダイレクト処理
 */
function redirectToLogin() {
    window.location.href = './login.html';
}

/**
 * パスワードリセット実行
 * @param {string} password - 新しいパスワード
 */
async function performResetPassword(password) {
    if (!resetToken) {
        showApiError('リセットリンクが無効です。もう一度パスワードリセットを行ってください。');
        return;
    }

    setLoading(true);
    clearApiMessage();

    try {
        const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: resetToken,
                new_password: password,
            }),
        });

        if (!response.ok) {
            if (response.status === 400) {
                showApiError('リンクが無効または期限切れです。再度パスワードリセットを行ってください');
            } else {
                showApiError('パスワード更新に失敗しました');
            }
            setLoading(false);
            return;
        }

        showApiSuccess('パスワードが更新されました');
        setTimeout(redirectToLogin, 1500);

    } catch (error) {
        console.error('パスワードリセットエラー:', error);
        showApiError('ネットワークエラーが発生しました。もう一度お試しください。');
        setLoading(false);
    }
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

    const password = passwordInput.value;
    performResetPassword(password);
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
    if (!resetToken) {
        showApiError('リセットリンクが無効です。もう一度パスワードリセットを行ってください。');
        submitButton.disabled = true;
        return;
    }

    resetPasswordForm.addEventListener('submit', handleSubmit);
    passwordInput.addEventListener('blur', handlePasswordBlur);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
