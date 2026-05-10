/**
 * LamGen Mini Games Hub Engine - V4 Mobile-First Universal Engine
 * Handles modal orchestration, HUD management, and lifecycle.
 */

const GamesHub = (() => {
    let currentGame = null;
    let currentSlug = null;
    let stage = null;
    let modal = null;
    let helperEl = null;
    let actionEl = null;
    
    let playMode = 'solo'; // solo, multi
    let rtc = null;
    let roomCode = null;
    let isHost = false;
    let onWsMessage = null;

    const profile = JSON.parse(localStorage.getItem('lamgen_arcade_profile_v4') || JSON.stringify({
        xp: 0,
        level: 1,
        streak: 0,
        lastPlayed: null,
        history: {},
        achievements: []
    }));

    const cacheDom = () => {
        modal = document.getElementById('gameModal');
        stage = document.getElementById('gameStage');
        helperEl = document.getElementById('gameHelperText');
        actionEl = document.getElementById('gameActionArea');
        return Boolean(modal && stage && helperEl && actionEl);
    };

    const init = () => {
        cacheDom();
        
        if (!modal || !stage || !helperEl || !actionEl) {
            console.warn('GamesHub init aborted: missing game modal markup. Make sure games/modal.html is included in the page.');
            return;
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
                close();
            }
        });
        checkStreak();
    };

    const getRank = (xp) => {
        let current = window.GameData.ranks[0];
        for (const r of window.GameData.ranks) {
            if (xp >= r.xp) current = r;
        }
        return current;
    };

    const checkStreak = () => {
        const today = new Date().toDateString();
        if (profile.lastPlayed !== today) {
            if (profile.lastPlayed) {
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);
                if (profile.lastPlayed === yesterday.toDateString()) {
                    profile.streak += 1;
                } else {
                    profile.streak = 1;
                }
            } else {
                profile.streak = 1;
            }
            profile.lastPlayed = today;
            saveProfile();
        }
    };

    const saveProfile = () => {
        localStorage.setItem('lamgen_arcade_profile_v4', JSON.stringify(profile));
        updateHUD();
    };

    const addXP = (amount) => {
        const oldRank = getRank(profile.xp);
        const day = new Date().getDay();
        const multiplier = (day === 0 || day === 6) ? 1.5 : 1;
        
        profile.xp += Math.round(amount * multiplier);
        const newRank = getRank(profile.xp);

        if (oldRank.name !== newRank.name) {
            showCinematic(`RANK UP: ${newRank.name}`, newRank.color);
            if (navigator.vibrate) navigator.vibrate([100, 50, 100, 50, 200]);
        }
        saveProfile();
    };

    const addToHistory = (game, id) => {
        if (!profile.history[game]) profile.history[game] = [];
        profile.history[game].push(id);
        if (profile.history[game].length > 50) profile.history[game].shift();
        saveProfile();
    };

    const hasSeen = (game, id) => {
        return profile.history[game] && profile.history[game].includes(id);
    };

    const showCinematic = (msg, color) => {
        const modalContent = document.querySelector('.game-modal-content');
        if (!modalContent) return;

        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: absolute; inset: 0; z-index: 999999;
            background: radial-gradient(circle, ${color}44 0%, rgba(0,0,0,0.9) 100%);
            display: flex; align-items: center; justify-content: center;
            opacity: 0; transition: opacity 0.3s; pointer-events: none;
        `;
        overlay.innerHTML = `<h1 style="font-family:'Syne',sans-serif; font-size:clamp(2rem, 8vw, 4rem); color:#fff; text-shadow:0 0 40px ${color}, 0 0 80px ${color}; transform:scale(0.5); transition:transform 0.5s cubic-bezier(0.34,1.56,0.64,1); text-align:center; padding:20px;">${msg}</h1>`;
        modalContent.appendChild(overlay);
        
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            overlay.querySelector('h1').style.transform = 'scale(1)';
        });

        setTimeout(() => {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 500);
        }, 2000);
    };

    const updateHUD = () => {
        const hud = document.getElementById('arcade-hud');
        if (hud) {
            const rank = getRank(profile.xp);
            hud.innerHTML = `
                <div style="display:flex; gap:16px; font-size:clamp(0.7rem, 2.5vw, 0.85rem); color:var(--lg-text-muted); align-items:center;">
                    <span style="color:${rank.color}; font-weight:800; font-family:'Syne',sans-serif; text-transform:uppercase;">${rank.name}</span>
                    <span>XP: <span style="color:var(--lg-text); font-weight:700;">${profile.xp}</span></span>
                </div>
                <div style="color:var(--lg-warning); font-weight:700; display:flex; align-items:center; gap:4px; font-size:clamp(0.7rem, 2.5vw, 0.85rem);">
                    <i class="bi bi-fire"></i> ${profile.streak}
                </div>
            `;
        }
    };

    const launch = (gameSlug) => {
        const game = window.GAMES_DATA.find(g => g.slug === gameSlug);
        if (!game) return;

        if (!cacheDom()) {
            console.warn('GamesHub launch aborted: game modal is not available.');
            return;
        }

        currentSlug = gameSlug;
        const titleEl = document.getElementById('gameTitle');
        const iconEl = document.getElementById('gameIcon');
        if (!titleEl || !iconEl) {
            console.warn('GamesHub launch aborted: game header markup is not available.');
            return;
        }

        titleEl.innerText = game.name;
        iconEl.innerHTML = `<i class="${game.icon}"></i>`;
        iconEl.style.background = `${game.color}22`;
        iconEl.style.color = game.color;

        updateHUD();
        setMode('solo');

        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    };

    const setMode = (mode) => {
        if (!cacheDom()) return;

        const soloBtn = document.getElementById('btn-mode-solo');
        const multiBtn = document.getElementById('btn-mode-multi');
        if (!soloBtn || !multiBtn) return;

        playMode = mode;
        soloBtn.className = `mode-btn ${mode === 'solo' ? 'active' : ''}`;
        multiBtn.className = `mode-btn ${mode === 'multi' ? 'active' : ''}`;
        
        soloBtn.style.background = mode === 'solo' ? 'var(--lg-violet)' : 'transparent';
        soloBtn.style.color = mode === 'solo' ? '#fff' : 'var(--lg-text-muted)';
        
        multiBtn.style.background = mode === 'multi' ? 'var(--lg-violet)' : 'transparent';
        multiBtn.style.color = mode === 'multi' ? '#fff' : 'var(--lg-text-muted)';

        if (currentGame && currentGame.destroy) currentGame.destroy();
        cleanupMultiplayer();

        if (mode === 'solo') {
            loadGame(currentSlug, false);
        } else {
            showMultiplayerLobby();
        }
    };

    const showMultiplayerLobby = () => {
        stage.innerHTML = `
            <div style="text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:20px;">
                <div style="font-size:3rem; color:var(--lg-violet);"><i class="bi bi-people-fill"></i></div>
                <h3 style="margin:0; font-family:'Syne',sans-serif; color:var(--lg-text);">Multiplayer Lobby</h3>
                <div style="display:flex; flex-direction:column; gap:12px; width:100%; max-width:300px;">
                    <button class="btn-mobile-primary" onclick="GamesHub.createRoom()">CREATE ROOM</button>
                    <div style="display:flex; gap:8px;">
                        <input type="text" id="join-code" placeholder="ENTER CODE" maxlength="4" style="flex:1; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:12px; color:#fff; text-align:center; font-weight:bold; text-transform:uppercase; font-size:1.2rem;">
                        <button class="btn-mobile-secondary" style="width:80px;" onclick="GamesHub.joinRoom()">JOIN</button>
                    </div>
                </div>
            </div>
        `;
        helperEl.innerText = "Play live with a friend.";
        actionEl.innerHTML = '';
    };

    const cleanupMultiplayer = () => {
        if (currentGame && currentGame.destroy) currentGame.destroy();
        if (rtc) rtc.destroy();
        rtc = null;
        roomCode = null;
        onWsMessage = null;
    };

    const createRoom = async () => {
        isHost = true;
        rtc = new RTCManager();
        rtc.onStatusChange = (status) => handleRTCStatus(status);
        rtc.onMessage = (data) => { if (onWsMessage) onWsMessage(data); };
        
        const code = await rtc.createRoom();
        roomCode = code;
        
        stage.innerHTML = `
            <div style="text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:20px;">
                <div class="pulse-icon" style="font-size:4rem; color:var(--lg-violet);"><i class="bi bi-broadcast"></i></div>
                <h3 style="margin:0; font-family:'Syne',sans-serif; color:var(--lg-text);">Waiting for Peer...</h3>
                <div style="background:rgba(255,255,255,0.05); padding:15px 30px; border-radius:16px; border:1px solid var(--lg-violet-bright);">
                    <div style="font-size:0.8rem; color:var(--lg-text-muted); margin-bottom:5px;">INVITE CODE</div>
                    <div style="font-size:2.5rem; font-weight:900; letter-spacing:5px; color:var(--lg-violet-bright);">${roomCode}</div>
                </div>
                <p style="color:var(--lg-text-muted); font-size:0.9rem;">Code copied to clipboard. Share it with a friend.</p>
            </div>
        `;
        helperEl.innerText = "Broadcasting P2P signal...";
    };

    const joinRoom = async () => {
        const code = document.getElementById('join-code').value.trim().toUpperCase();
        if (code.length !== 4) {
            helperEl.innerText = "Invalid room code.";
            return;
        }
        isHost = false;
        rtc = new RTCManager();
        rtc.onStatusChange = (status) => handleRTCStatus(status);
        rtc.onMessage = (data) => { if (onWsMessage) onWsMessage(data); };
        
        await rtc.joinRoom(code);
        roomCode = code;
        helperEl.innerText = "Negotiating peer connection...";
    };

    const handleRTCStatus = (status) => {
        if (status === 'connected') {
            loadGame(currentSlug, true);
        } else if (status === 'disconnected' || status === 'failed') {
            stage.innerHTML = `
                <div style="text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:20px;">
                    <div style="font-size:4rem; color:var(--lg-danger);"><i class="bi bi-exclamation-triangle-fill"></i></div>
                    <h3 style="margin:0; font-family:'Syne',sans-serif; color:var(--lg-text);">P2P Error</h3>
                    <p style="color:var(--lg-text-muted); padding:0 20px;">The direct peer connection failed. This usually happens on restrictive public networks.</p>
                    <button class="btn-mobile-primary" onclick="GamesHub.setMode('multi')">TRY AGAIN</button>
                </div>
            `;
            helperEl.innerText = "Connection lost.";
        }
    };

    const loadGame = (slug, isMulti) => {
        if (!cacheDom()) return;

        if (currentGame && currentGame.destroy) currentGame.destroy();
        stage.innerHTML = '';
        helperEl.innerText = '';
        actionEl.innerHTML = '';
        
        if (typeof GameEngines[slug] === 'function') {
            const api = {
                addXP: addXP,
                addToHistory: (id) => addToHistory(slug, id),
                hasSeen: (id) => hasSeen(slug, id),
                saveScore: (score) => saveScore(slug, score),
                getBestScore: () => getBestScore(slug),
                showCinematic: showCinematic,
                rank: getRank(profile.xp),
                isMulti: isMulti,
                isHost: isHost,
                roomCode: roomCode,
                sendWS: (action, payload) => {
                    if (rtc) rtc.send(action, payload);
                },
                onWS: (cb) => { onWsMessage = cb; }
            };
            currentGame = new GameEngines[slug](stage, helperEl, actionEl, api);
            currentGame.start();
            
            if (isMulti && isHost) {
                // Auto-copy invite
                navigator.clipboard.writeText(roomCode).catch(e=>{});
            }
        } else {
            helperEl.innerText = 'Engine offline.';
        }
    };

    const close = () => {
        if (currentGame && currentGame.destroy) currentGame.destroy();
        cleanupMultiplayer();
        if (modal) modal.style.display = 'none';
        document.body.style.overflow = '';
        currentGame = null;
    };

    const restart = () => {
        if (currentGame && currentGame.destroy) currentGame.destroy();
        if (currentGame) currentGame.start();
    };

    const saveScore = (gameSlug, score) => {
        const scores = JSON.parse(localStorage.getItem('lamgen_game_scores_v4') || '{}');
        if (!scores[gameSlug] || score > scores[gameSlug]) {
            scores[gameSlug] = score;
            localStorage.setItem('lamgen_game_scores_v4', JSON.stringify(scores));
            return true;
        }
        return false;
    };

    const getBestScore = (gameSlug) => {
        const scores = JSON.parse(localStorage.getItem('lamgen_game_scores_v4') || '{}');
        return scores[gameSlug] || 0;
    };

    return { init, launch, close, restart, setMode, createRoom, joinRoom };
})();

window.GamesHub = GamesHub;
window.launchGame = GamesHub.launch;
window.closeGame = GamesHub.close;
window.restartGame = GamesHub.restart;

document.addEventListener('DOMContentLoaded', GamesHub.init);
