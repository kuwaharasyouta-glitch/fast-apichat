// APIのベースURL
const API_BASE_URL = "";

// WebSocketコネクション
let socket = null;

let currentUsername = null;

// UI表示切替関数
function showLogin() {
  const loginContainer = document.getElementById("login-container");
  const registerContainer = document.getElementById("register-container");
  const chatContainer = document.getElementById("chat-container");

  if (loginContainer) loginContainer.style.display = "block";
  if (registerContainer) registerContainer.style.display = "none";
  if (chatContainer) chatContainer.style.display = "none";
  console.log("Showing login form");
}

function showRegister() {
  const loginContainer = document.getElementById("login-container");
  const registerContainer = document.getElementById("register-container");
  const chatContainer = document.getElementById("chat-container");

  if (loginContainer) loginContainer.style.display = "none";
  if (registerContainer) registerContainer.style.display = "block";
  if (chatContainer) chatContainer.style.display = "none";
  console.log("Showing register form");
}

function showChat() {
  const loginContainer = document.getElementById("login-container");
  const registerContainer = document.getElementById("register-container");
  const chatContainer = document.getElementById("chat-container");
  const loggedInUser = document.getElementById("logged-in-user");

  if (loginContainer) loginContainer.style.display = "none";
  if (registerContainer) registerContainer.style.display = "none";
  if (chatContainer) chatContainer.style.display = "block";

  if (currentUsername && loggedInUser) {
    loggedInUser.textContent = `${currentUsername} としてログイン中`;
  }
  console.log("Showing chat container");
}

function logout() {
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  currentUsername = null;

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.close();
    socket = null;
  }
  showLogin();
}

// メッセージ送信
function sendMessage(messageText) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    alert("WebSocket接続がありません。");
    return;
  }

  // メッセージ送信のみを行う（表示は行わない - サーバーからのブロードキャストで表示される）
  socket.send(messageText);

  // 入力フィールドをクリア
  const messageInput = document.getElementById("messageInput");
  if (messageInput) messageInput.value = "";
}

// メッセージをエリアに追加
function addMessage(text, className = "message") {
  const messagesArea = document.getElementById("messagesArea");
  if (!messagesArea) {
    console.error("Messages area not found");
    return;
  }

  const div = document.createElement("div");
  div.textContent = text;
  div.className = className;
  messagesArea.appendChild(div);

  // 確実に一番下までスクロール
  setTimeout(() => {
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }, 10);
}

// WebSocketを使ったログイン
function loginUser(username, password) {
  // 既存の接続を閉じる
  if (socket) {
    socket.close();
    socket = null;
  }

  // WebSocket接続
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${location.host}/ws`);

  socket.onopen = () => {
    // 接続が確立したら認証情報を送信
    socket.send(
      JSON.stringify({
        username: username,
        password: password,
      })
    );
    //addMessage("WebSocket接続を確立しました。認証中...", "system-message");
  };

  // メッセージ受信時の処理
  socket.onmessage = (event) => {
    try {
      // JSONとしてパースを試みる
      const data = JSON.parse(event.data);

      if (data.token) {
        // 認証成功の処理
        console.log("認証成功:", data);
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify({ username }));

        currentUsername = username;  

        //addMessage("認証成功: WebSocketに接続しました", "system-message");
        showChat();
      } else if (data.type === "message") {
        // メッセージの表示
        console.log("メッセージ受信:", data);

        // メッセージクラスを決定
        let messageClass = "message";

        // AIメッセージか通常メッセージかで表示クラスを変える
        if (data.is_ai) {
          messageClass += " ai-message";
        } else {
          // 自分のメッセージかどうかで表示スタイルを変える
          const user = JSON.parse(
            localStorage.getItem("user") || '{"username":""}'
          );
          if (data.username === currentUsername) {
              messageClass += " user-message";
          } else {
              messageClass += " other-message";
          }
        }

        addMessage(`${data.username}: ${data.content}`, messageClass);
      } else if (data.type === "system") {
        // システムメッセージ
        console.log("システムメッセージ:", data);
        addMessage(data.content, "system-message");
      } else {
        // その他のJSONデータ
        console.log("その他のJSONデータ:", data);
        if (data.message) {
          addMessage(data.message, "system-message");
        } else if (data.error) {
          console.error(data.error);
        } else {
          addMessage(JSON.stringify(data), "system-message");
        }
      }
    } catch (e) {
      // JSON以外のテキストメッセージ
      console.log("テキストメッセージ:", event.data, e);
      addMessage(event.data, "system-message");
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocketエラー:", error);
  };

  socket.onclose = (event) => {
    console.log("WebSocket切断:", event);
    if (event.code === 1008) {
      alert("認証エラー: " + event.reason);
    } else if (event.code !== 1000) {
      // 正常終了以外の場合
      
    }
  };
}

// API呼び出し関数：ユーザー登録
async function registerUser(username, email, password) {
  try {
    console.log("Registering user:", username);
    const response = await fetch(`${API_BASE_URL}/user`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `エラー: ${response.status}`);
    }

    const data = await response.json();
    alert("登録が完了しました。ログインしてください。");
    showLogin();
  } catch (error) {
    alert("登録に失敗しました: " + error.message);
  }
}

// ページ読み込み時の初期化処理
function initializeApp() {
  console.log("Initializing app");

  // 送信ボタンイベント
  const sendButton = document.getElementById("sendButton");
  if (sendButton) {
    sendButton.addEventListener("click", () => {
      const messageInput = document.getElementById("messageInput");
      if (messageInput) {
        const msg = messageInput.value.trim();
        if (msg) {
          sendMessage(msg);
        }
      }
    });
    console.log("Send button listener set");
  } else {
    console.error("Send button not found");
  }

  // ウィンドウサイズ変更時にもスクロール位置を調整
  window.addEventListener("resize", function () {
    const messagesArea = document.getElementById("messagesArea");
    if (messagesArea) {
      messagesArea.scrollTop = messagesArea.scrollHeight;
    }
  });

  // Enter キーでも送信できるようにする
  const messageInput = document.getElementById("messageInput");
  if (messageInput) {
    messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        const msg = messageInput.value.trim();
        if (msg) {
          sendMessage(msg);
        }
      }
    });
    console.log("Message input keypress listener set");
  } else {
    console.error("Message input not found during initialization");
  }

  // ローカルストレージからユーザー情報とトークンを取得
  localStorage.removeItem("user");
  localStorage.removeItem("token");
  currentUsername = null;
  showLogin();
}

// DOM読み込み完了時の処理
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM loaded");

  // ログインフォームのイベントリスナー設定
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
      loginUser(username, password);
    });
    console.log("Login form listener set");
  } else {
    console.error("Login form not found");
  }

  // 登録フォームのイベントリスナー設定
  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("reg-username").value;
      const email = document.getElementById("reg-email").value;
      const password = document.getElementById("reg-password").value;
      await registerUser(username, email, password);
    });
    console.log("Register form listener set");
  } else {
    console.error("Register form not found");
  }

  // ログアウトボタンのイベントリスナー設定
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
    console.log("Logout button listener set");
  } else {
    console.error("Logout button not found");
  }

  // 「新規登録はこちら」リンクのイベントリスナー設定
  const showRegisterLink = document.getElementById("show-register");
  if (showRegisterLink) {
    showRegisterLink.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Show register link clicked");
      showRegister();
    });
    console.log("Show register link listener set");
  } else {
    console.error("Show register link not found");
  }

  // 「ログインに戻る」リンクのイベントリスナー設定
  const showLoginLink = document.getElementById("show-login");
  if (showLoginLink) {
    showLoginLink.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Show login link clicked");
      showLogin();
    });
    console.log("Show login link listener set");
  } else {
    console.error("Show login link not found");
  }

  // アプリの初期化処理を実行
  initializeApp();
});