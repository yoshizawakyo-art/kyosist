/**
 * Kyosist パスワードリセット申請フォーム
 * メールアドレスを入力してリセットリンク送信を要求する。
 * 成功時はログイン画面へ自動遷移する。
 */

const API_BASE_URL = '/api';

const forgotPasswordForm = document.getElementById('forgotPasswordForm');
const emailInput = document.getElementById('email');
const submitButton = document.getElementById('submitButton');
const spinner = document.getElementById('spinner');
const emailError = document.getElementById('emailError');
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
 * フォームバリデーション実行
 * @returns {boolean} すべてのフィールドが有効な場合true
 */
function validateForm() {
    let isValid = true;

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
 * APIエラー・成功表示をクリアする
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
 * リセットリンク送信成功時のリダイレクト処理
 */
function redirectToLogin() {
    window.location.href = './login.html';
}

/**
 * パスワードリセット申請を実行する
 * @param {string} email - メールアドレス
 */
async function performForgotPassword(email) {
    setLoading(true);
    clearApiMessage();

    try {
        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
            }),
        });

        if (!response.ok) {
            if (response.status === 400) {
                showApiError('無効なメールアドレスです');
            } else {
                showApiError('リクエストに失敗しました');
            }
            setLoading(false);
            return;
        }

        showApiSuccess('リセットリンクが送信されました。メールをご確認ください。');
        setTimeout(redirectToLogin, 1500);

    } catch (error) {
        console.error('パスワードリセット申請エラー:', error);
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

    const email = emailInput.value.trim();
    performForgotPassword(email);
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
 * 初期化処理
 */
function init() {
    forgotPasswordForm.addEventListener('submit', handleSubmit);
    emailInput.addEventListener('blur', handleEmailBlur);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
