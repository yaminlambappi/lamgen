/**
 * Game Engines for LamGen Mini Games Hub - V4 Mobile-First Universal Engine
 * Responsive, touch-first, and highly accessible game loop implementations.
 */

const GameEngines = {};

const vibrate = (ms) => {
    if (navigator.vibrate) navigator.vibrate(ms);
};

// ── Game 1: Reaction Test (Chaos Arcade) ──
GameEngines['reaction-test'] = class {
    constructor(stage, helper, action, api) {
        this.stage = stage;
        this.helper = helper;
        this.action = action;
        this.api = api;
        this.state = 'idle'; 
        this.startTime = 0;
        this.timeout = null;
        this.destroyed = false;
        this.combo = 0;
        this.score = 0;
    }

    destroy() {
        this.destroyed = true;
        clearTimeout(this.timeout);
        this.stage.onclick = null;
    }

    start() {
        this.combo = 0;
        this.score = 0;
        
        this.stage.innerHTML = `
            <div id="rt-target" style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; border-radius:16px; background:rgba(255,255,255,0.02); border:2px solid rgba(255,255,255,0.05); transition:all 0.1s; cursor:pointer; user-select:none; -webkit-tap-highlight-color:transparent;">
                <div id="rt-msg" style="font-family:'Syne',sans-serif; font-size:clamp(1.5rem, 5vw, 2.5rem); font-weight:800; text-align:center;">TAP TO START</div>
            </div>
            <div style="position:absolute; top:20px; right:20px; font-weight:bold; font-size:clamp(1rem, 3vw, 1.2rem); color:var(--lg-cyan);" id="rt-score">Score: 0</div>
            <div style="position:absolute; top:20px; left:20px; font-weight:bold; font-size:clamp(1rem, 3vw, 1.2rem); color:var(--lg-warning);" id="rt-combo">Combo: x0</div>
        `;
        
        this.target = document.getElementById('rt-target');
        this.msg = document.getElementById('rt-msg');
        
        this.stage.onclick = () => this.handleClick();
        
        this.helper.innerText = `High Score: ${this.api.getBestScore()}`;
        this.action.innerHTML = `<button class="btn-mobile-secondary" onclick="restartGame()"><i class="bi bi-arrow-counterclockwise"></i></button>`;
    }

    handleClick() {
        if (this.destroyed) return;

        if (this.state === 'idle') {
            this.triggerWait();
        } else if (this.state === 'waiting') {
            vibrate([50, 100, 50]);
            this.fail("TOO EARLY!");
        } else if (this.state === 'fakeout') {
            vibrate([50, 100, 50]);
            this.fail("FAKE OUT!");
        } else if (this.state === 'ready') {
            vibrate(50);
            const rt = Date.now() - this.startTime;
            this.state = 'result';
            
            this.combo++;
            let points = Math.max(10, (1000 - rt)) * this.combo;
            this.score += points;
            this.api.addXP(Math.round(points / 20));

            this.target.style.background = 'rgba(62,236,216,0.2)';
            this.target.style.borderColor = '#3EECD8';
            this.msg.innerHTML = `${rt}<span style="font-size:0.5em;">ms</span>`;
            
            this.api.saveScore(this.score);
            document.getElementById('rt-score').innerText = `Score: ${this.score}`;
            document.getElementById('rt-combo').innerText = `Combo: x${this.combo}`;
            
            this.helper.innerText = `+${points} XP`;

            if (this.combo > 0 && this.combo % 10 === 0) {
                this.api.showCinematic(`${this.combo} COMBO!`, '#F59E0B');
            }

            setTimeout(() => {
                if(!this.destroyed) this.triggerWait();
            }, 800);
        } else if (this.state === 'result') {
            this.triggerWait();
        }
    }

    fail(reason) {
        clearTimeout(this.timeout);
        this.state = 'result';
        this.combo = 0;
        this.target.style.background = 'rgba(255,92,122,0.2)';
        this.target.style.borderColor = '#FF5C7A';
        this.msg.innerHTML = `<span style="font-size:0.8em;">${reason}</span>`;
        this.helper.innerText = "Combo Reset. Tap to restart round.";
        document.getElementById('rt-combo').innerText = `Combo: x0`;
    }

    triggerWait() {
        this.state = 'waiting';
        this.target.style.background = 'rgba(239,68,68,0.05)';
        this.target.style.borderColor = 'rgba(239,68,68,0.2)';
        this.msg.innerText = 'WAIT...';
        this.helper.innerText = "Get ready...";
        
        let isFake = (this.combo > 3 && Math.random() < 0.25);
        let delay = (2000 * Math.max(0.2, 1 - (this.combo * 0.05))) + (Math.random() * 2000);
        
        this.timeout = setTimeout(() => {
            if (isFake) this.setFakeOut();
            else this.setReady();
        }, delay);
    }

    setFakeOut() {
        if (this.destroyed) return;
        this.state = 'fakeout';
        this.target.style.background = 'rgba(245,158,11,0.2)'; // Orange
        this.target.style.borderColor = '#F59E0B';
        this.msg.innerText = 'TAP!';
        this.timeout = setTimeout(() => {
            if (this.state === 'fakeout') {
                this.state = 'waiting';
                this.target.style.background = 'rgba(239,68,68,0.05)';
                this.target.style.borderColor = 'rgba(239,68,68,0.2)';
                this.msg.innerText = 'WAIT...';
                this.timeout = setTimeout(() => this.setReady(), 1000 + Math.random()*1500);
            }
        }, 300);
    }

    setReady() {
        if (this.destroyed) return;
        this.state = 'ready';
        this.startTime = Date.now();
        this.target.style.background = '#3EECD8';
        this.target.style.borderColor = '#3EECD8';
        this.target.style.color = '#000';
        this.msg.innerText = 'TAP NOW!';
        this.helper.innerText = "TAP!";
        
        const allowedTime = Math.max(300, 1500 - (this.combo * 50));
        this.timeout = setTimeout(() => {
            if (this.state === 'ready') this.fail("TOO SLOW!");
        }, allowedTime);
    }
};

// ── Game 2: Typing Duel (Mobile-First Survival) ──
GameEngines['typing-duel'] = class {
    constructor(stage, helper, action, api) {
        this.stage = stage;
        this.helper = helper;
        this.action = action;
        this.api = api;
        this.destroyed = false;
        
        this.activeWords = [];
        this.score = 0;
        this.multiplier = 1;
        this.gameLoop = null;
        this.spawnRate = 2500;
        this.lastSpawn = 0;
        this.speedMultiplier = 0.5;
        this.lives = 3;
    }

    destroy() {
        this.destroyed = true;
        cancelAnimationFrame(this.gameLoop);
        if(this.input) this.input.oninput = null;
    }

    generatePhrase() {
        const data = window.GameData.typing;
        const roll = Math.random();
        if (roll < 0.3) {
            const s = data.absurdFragments.subjects;
            const a = data.absurdFragments.actions;
            const e = data.absurdFragments.endings;
            return `${s[Math.floor(Math.random()*s.length)]} ${a[Math.floor(Math.random()*a.length)]} ${e[Math.floor(Math.random()*e.length)]}`;
        } else if (roll < 0.6) {
            return data.categories.genZ[Math.floor(Math.random()*data.categories.genZ.length)];
        } else {
            return data.categories.toxic[Math.floor(Math.random()*data.categories.toxic.length)];
        }
    }

    start() {
        this.stage.innerHTML = `
            <div id="td-canvas" style="position:absolute; inset:0; padding-top:40px;"></div>
            <div style="position:absolute; top:10px; right:15px; font-weight:bold; font-size:clamp(1rem, 3vw, 1.2rem); color:var(--lg-violet-bright);" id="td-score">0</div>
            <div style="position:absolute; top:10px; left:15px; font-weight:bold; font-size:clamp(1rem, 3vw, 1.2rem); color:var(--lg-warning);" id="td-multi">x1</div>
            <div style="position:absolute; top:35px; right:15px; font-size:1rem;" id="td-lives">❤️❤️❤️</div>
        `;
        
        this.helper.innerText = "Type the falling text correctly.";
        
        // Pinned input for mobile keyboards
        this.action.innerHTML = `
            <input type="text" id="td-input" placeholder="Type here..." autofocus 
                style="width:100%; padding:14px 20px; border-radius:12px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.2); color:#fff; font-size:16px; outline:none; box-shadow:inset 0 2px 4px rgba(0,0,0,0.5);" 
                autocomplete="off" autocorrect="off" autocapitalize="none">
        `;

        this.canvas = document.getElementById('td-canvas');
        this.input = document.getElementById('td-input');
        this.scoreEl = document.getElementById('td-score');
        this.multiEl = document.getElementById('td-multi');
        this.livesEl = document.getElementById('td-lives');
        
        this.input.oninput = () => this.handleInput();

        this.activeWords = [];
        this.score = 0;
        this.multiplier = 1;
        this.speedMultiplier = 0.5; 
        this.spawnRate = 3000;
        this.lives = 3;
        this.lastSpawn = performance.now();
        
        this.gameLoop = requestAnimationFrame((t) => this.loop(t));
    }

    spawnWord() {
        let text = this.generatePhrase().toLowerCase(); // Normalize for mobile typing
        const el = document.createElement('div');
        el.innerHTML = text.split('').map(c => `<span>${c}</span>`).join('');
        el.style.position = 'absolute';
        
        const offset = Math.random() * 20 + 5; 
        el.style.left = `${offset}%`;
        el.style.top = '-40px';
        el.style.fontFamily = 'monospace';
        el.style.fontSize = 'clamp(0.8rem, 2.5vw, 1rem)';
        el.style.color = 'var(--lg-text-muted)';
        el.style.padding = '6px 12px';
        el.style.background = 'rgba(10,8,26,0.9)';
        el.style.borderRadius = '8px';
        el.style.border = '1px solid rgba(139,127,255,0.3)';
        el.style.maxWidth = '80%';
        el.style.wordWrap = 'break-word';
        el.style.lineHeight = '1.4';
        
        this.canvas.appendChild(el);
        this.activeWords.push({ text, el, y: -40 });
    }

    loop(time) {
        if (this.destroyed) return;

        if (time - this.lastSpawn > this.spawnRate) {
            this.spawnWord();
            this.lastSpawn = time;
            this.spawnRate = Math.max(1500, this.spawnRate - 50); 
            this.speedMultiplier += 0.02;
        }

        let loseLife = false;
        for (let i = this.activeWords.length - 1; i >= 0; i--) {
            let w = this.activeWords[i];
            w.y += 1 * this.speedMultiplier;
            w.el.style.top = w.y + 'px';
            
            if (w.y > this.canvas.clientHeight - 40) {
                w.el.remove();
                this.activeWords.splice(i, 1);
                loseLife = true;
            }
        }

        if (loseLife) {
            vibrate(200);
            this.lives--;
            this.multiplier = 1;
            this.livesEl.innerText = "❤️".repeat(this.lives);
            this.stage.style.boxShadow = "inset 0 0 50px rgba(255,0,0,0.5)";
            setTimeout(() => { if(this.stage) this.stage.style.boxShadow = "none"; }, 200);

            if (this.lives <= 0) {
                this.endGame();
                return;
            }
        }

        this.gameLoop = requestAnimationFrame((t) => this.loop(t));
    }

    handleInput() {
        const val = this.input.value.trim().toLowerCase();
        let anyMatch = false;
        
        this.activeWords.forEach(w => {
            const spans = w.el.querySelectorAll('span');
            let matchedLen = 0;
            
            for(let i=0; i<w.text.length; i++) {
                if (i < val.length && w.text[i] === val[i]) {
                    spans[i].style.color = '#3EECD8';
                    matchedLen++;
                } else if (i < val.length && w.text[i] !== val[i]) {
                    spans[i].style.color = '#FF5C7A';
                } else {
                    spans[i].style.color = '';
                }
            }

            if (matchedLen > 0 && matchedLen === val.length) {
                anyMatch = true;
            }
        });

        for (let i = 0; i < this.activeWords.length; i++) {
            if (this.activeWords[i].text === val) {
                vibrate(30);
                this.activeWords[i].el.remove();
                this.activeWords.splice(i, 1);
                this.input.value = '';
                
                const pts = val.length * 10 * this.multiplier;
                this.score += pts;
                this.multiplier++;
                this.api.addXP(Math.round(pts / 5));
                anyMatch = true;
                break;
            }
        }

        if (!anyMatch && val.length > 0) {
            this.multiplier = 1;
        }

        this.scoreEl.innerText = this.score;
        this.multiEl.innerText = 'x' + this.multiplier;
    }

    endGame() {
        this.destroyed = true; 
        this.api.saveScore(this.score);
        this.stage.innerHTML = `
            <div style="text-align:center;">
                <h2 style="color:var(--lg-danger); font-size:clamp(2rem, 8vw, 3rem); font-family:'Syne',sans-serif; margin:0;">BREACHED</h2>
                <p style="color:var(--lg-text-muted);">Score: ${this.score}</p>
            </div>
        `;
        this.helper.innerText = `High Score: ${this.api.getBestScore()}`;
        this.action.innerHTML = `<button class="btn-mobile-primary" onclick="restartGame()">REBOOT</button>`;
    }
};

// ── Game 3: Would You Rather (Prediction Mode) ──
GameEngines['would-you-rather'] = class {
    constructor(stage, helper, action, api) {
        this.stage = stage;
        this.helper = helper;
        this.action = action;
        this.api = api;
        this.destroyed = false;
        this.score = 0;
        this.streak = 0;
    }

    destroy() {
        this.destroyed = true;
    }

    start() {
        this.score = 0;
        this.streak = 0;
        this.nextRound();
    }

    generatePrompt() {
        const d = window.GameData.wyr;
        
        const buildStatement = () => {
            let tmpl = d.templates[Math.floor(Math.random() * d.templates.length)];
            const matches = tmpl.match(/\{([a-zA-Z_]+)\}/g) || [];
            matches.forEach(m => {
                const key = m.replace(/[{}]/g, '');
                if (d.components[key]) {
                    const pool = d.components[key];
                    const word = pool[Math.floor(Math.random() * pool.length)];
                    tmpl = tmpl.replace(m, word);
                }
            });
            return tmpl;
        };

        const a = buildStatement();
        let b = buildStatement();
        
        // Prevent identical statements
        let safety = 0;
        while (b === a && safety < 10) {
            b = buildStatement();
            safety++;
        }
        
        if (Math.random() > 0.5) {
            const mod = d.modifiers[Math.floor(Math.random() * d.modifiers.length)];
            b += mod;
        }
        
        const id = a + "|" + b;
        if (this.api.hasSeen(id)) return this.generatePrompt();
        this.api.addToHistory(id);
        
        return { a, b };
    }

    nextRound() {
        if(this.destroyed) return;
        
        if (this.api.isMulti) {
            if (this.api.isHost) {
                const p = this.generatePrompt();
                const globalA = Math.floor(Math.random() * 80) + 10;
                const payload = { p, globalA };
                this.api.sendWS('sync_round', payload);
                this.renderRound(payload.p, payload.globalA);
            } else {
                this.helper.innerText = "Waiting for Host...";
                this.api.onWS((data) => {
                    if (data.action === 'sync_round') {
                        this.renderRound(data.payload.p, data.payload.globalA);
                    }
                    if (data.action === 'sync_score') {
                        this.opponentScore = data.payload;
                        this.updateHUD();
                    }
                });
            }
        } else {
            const p = this.generatePrompt();
            const globalA = Math.floor(Math.random() * 80) + 10;
            this.renderRound(p, globalA);
        }
    }

    renderRound(p, globalA) {
        this.fakeGlobalA = globalA;
        this.fakeGlobalB = 100 - this.fakeGlobalA;

        this.stage.innerHTML = `
            <div style="width:100%; max-width:400px; display:flex; flex-direction:column; gap:16px;">
                <div id="wyr-left" class="wyr-card touch-target" style="background:rgba(62,236,216,0.05); border:2px solid rgba(62,236,216,0.2);">
                    <div class="wyr-content">${p.a}</div>
                    <div class="wyr-fill" style="background:rgba(62,236,216,0.15);"></div>
                    <div class="wyr-percent"></div>
                </div>
                
                <div style="font-family:'Syne',sans-serif; font-weight:800; opacity:0.3; font-size:1.2rem; text-align:center;">OR</div>
                
                <div id="wyr-right" class="wyr-card touch-target" style="background:rgba(139,127,255,0.05); border:2px solid rgba(139,127,255,0.2);">
                    <div class="wyr-content">${p.b}</div>
                    <div class="wyr-fill" style="background:rgba(139,127,255,0.15);"></div>
                    <div class="wyr-percent"></div>
                </div>
            </div>

            <style>
                .wyr-card {
                    position: relative; overflow: hidden; border-radius: 20px;
                    padding: clamp(1.5rem, 5vw, 2.5rem) 1.5rem;
                    text-align: center; font-weight: 700; font-size: clamp(1rem, 4vw, 1.2rem);
                    cursor: pointer; transition: transform 0.1s, border-color 0.3s;
                    display: flex; align-items: center; justify-content: center; min-height: 120px;
                }
                .wyr-card:active { transform: scale(0.98); }
                .wyr-content { position: relative; z-index: 2; line-height: 1.4; }
                .wyr-fill { position: absolute; bottom: 0; left: 0; width: 0%; height: 100%; transition: width 1s cubic-bezier(0.34,1.56,0.64,1); }
                .wyr-percent { position: absolute; right: 15px; bottom: 10px; font-size: 2rem; font-weight: 800; opacity: 0; z-index: 2; font-family: 'Syne', sans-serif; transition: opacity 0.5s; }
            </style>
        `;

        this.helper.innerText = `Which did the internet pick?`;
        this.updateHUD();

        const leftEl = document.getElementById('wyr-left');
        const rightEl = document.getElementById('wyr-right');
        
        leftEl.onclick = () => this.handlePick('A');
        rightEl.onclick = () => this.handlePick('B');
    }

    updateHUD() {
        let multiHUD = '';
        if (this.api.isMulti) {
            multiHUD = `<span style="font-weight:700; color:var(--lg-violet-bright);">Opponent: ${this.opponentScore || 0}</span>`;
        }
        this.action.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                <span style="font-weight:700; color:var(--lg-cyan);">Score: ${this.score}</span>
                ${multiHUD}
                <span style="font-weight:700; color:var(--lg-warning);"><i class="bi bi-fire"></i> Combo: ${this.streak}</span>
            </div>
        `;
    }

    handlePick(choice) {
        if(this.destroyed) return;
        
        const isLeft = choice === 'A';
        const pickedPercent = isLeft ? this.fakeGlobalA : this.fakeGlobalB;
        const otherPercent = isLeft ? this.fakeGlobalB : this.fakeGlobalA;
        const isMajority = pickedPercent >= otherPercent;
        
        const leftEl = document.getElementById('wyr-left');
        const rightEl = document.getElementById('wyr-right');
        
        leftEl.onclick = null; rightEl.onclick = null;
        
        // Animations
        leftEl.querySelector('.wyr-fill').style.width = `${this.fakeGlobalA}%`;
        const lp = leftEl.querySelector('.wyr-percent');
        lp.innerText = `${this.fakeGlobalA}%`; lp.style.opacity = '0.3';
        
        rightEl.querySelector('.wyr-fill').style.width = `${this.fakeGlobalB}%`;
        const rp = rightEl.querySelector('.wyr-percent');
        rp.innerText = `${this.fakeGlobalB}%`; rp.style.opacity = '0.3';

        if (isMajority) {
            vibrate(50);
            this.streak++;
            const pts = 50 * this.streak;
            this.score += pts;
            this.api.addXP(10 * this.streak);
            if (this.api.isMulti) this.api.sendWS('sync_score', this.score);
            this.helper.innerHTML = `<span style="color:var(--lg-success);">CORRECT! The internet agrees.</span>`;
            (isLeft ? leftEl : rightEl).style.borderColor = 'var(--lg-success)';
        } else {
            vibrate([50, 100, 50]);
            this.streak = 1;
            this.helper.innerHTML = `<span style="color:var(--lg-danger);">WRONG! You misjudged the internet.</span>`;
            (isLeft ? leftEl : rightEl).style.borderColor = 'var(--lg-danger)';
            leftEl.classList.add('shake-error'); rightEl.classList.add('shake-error');
        }

        this.api.saveScore(this.score);
        this.updateHUD();

        setTimeout(() => this.nextRound(), 2500);
    }
};

// ── Game 4: Memory Flash (Strict Deterministic FSM) ──
GameEngines['memory-flash'] = class {
    constructor(stage, helper, action, api) {
        this.stage = stage;
        this.helper = helper;
        this.action = action;
        this.api = api;
        
        this.STATES = {
            IDLE: 'IDLE',
            SHOWING: 'SHOWING_SEQUENCE',
            INPUT: 'WAITING_INPUT',
            FAIL: 'FAILURE',
            DEAD: 'DEAD'
        };
        
        this.state = this.STATES.IDLE;
        this.sequence = [];
        this.playerIndex = 0;
        this.score = 0;
        this.gridSize = 4;
        this.activeTimeouts = [];
        this.colors = ['#3EECD8', '#8B7FFF', '#FF5C7A', '#F59E0B', '#10B981', '#EC4899'];
    }

    logState(transition) {
        // console.log(`[MemoryFlash] State Transition: ${transition} | Current State: ${this.state} | SeqLength: ${this.sequence.length}`);
    }

    destroy() {
        this.state = this.STATES.DEAD;
        this.clearAllTimers();
    }

    clearAllTimers() {
        this.activeTimeouts.forEach(t => clearTimeout(t));
        this.activeTimeouts = [];
    }

    safeTimeout(fn, delay) {
        if (this.state === this.STATES.DEAD) return;
        const t = setTimeout(() => {
            if (this.state !== this.STATES.DEAD) fn();
        }, delay);
        this.activeTimeouts.push(t);
        return t;
    }

    start() {
        this.state = this.STATES.IDLE;
        this.sequence = [];
        this.score = 0;
        this.gridSize = 4;
        this.clearAllTimers();
        
        this.renderStage();
        this.showStartUI();
    }

    showStartUI() {
        this.action.innerHTML = `<button id="mf-init-btn" class="btn-mobile-primary">INITIALIZE SEQUENCE</button>`;
        const btn = document.getElementById('mf-init-btn');
        if (btn) btn.onclick = () => this.startRound();
        this.helper.innerText = `High Score: ${this.api.getBestScore()}`;
    }

    renderStage() {
        let cellsHTML = '';
        for(let i=0; i<this.gridSize; i++) {
            cellsHTML += `<div id="mf-${i}" data-idx="${i}" class="mf-cell touch-target" style="width:clamp(80px, 20vw, 120px); height:clamp(80px, 20vw, 120px); border-radius:16px; background:rgba(255,255,255,0.03); border:2px solid rgba(255,255,255,0.1); transition:transform 0.1s, box-shadow 0.2s;" data-color="${this.colors[i]}"></div>`;
        }

        let cols = this.gridSize <= 4 ? 2 : 3;

        this.stage.innerHTML = `
            <div id="mf-bg" style="position:absolute; inset:0; z-index:0; transition:background 0.5s;"></div>
            <div style="position:absolute; top:15px; right:15px; font-weight:bold; font-size:clamp(1rem, 3vw, 1.2rem); color:var(--lg-warning); z-index:2;">Score: <span id="mf-score">${this.score}</span></div>
            <div id="mf-grid" style="display:grid; grid-template-columns:repeat(${cols}, 1fr); gap:12px; perspective:1000px; transition:transform 0.5s; z-index:2;">
                ${cellsHTML}
            </div>
            <div id="mf-msg" style="position:absolute; bottom:20px; font-weight:800; font-size:clamp(1.5rem, 5vw, 2rem); color:var(--lg-text); font-family:'Syne',sans-serif; opacity:0; transition:opacity 0.3s; z-index:1;">LEVEL 1</div>
        `;
        
        this.bindEvents();
    }

    bindEvents() {
        document.querySelectorAll('.mf-cell').forEach(el => {
            el.ontouchstart = (e) => { e.preventDefault(); this.handlePlayerTap(parseInt(el.dataset.idx)); };
            el.onmousedown = () => this.handlePlayerTap(parseInt(el.dataset.idx));
        });
    }

    startRound() {
        if (this.state === this.STATES.DEAD || this.state === this.STATES.SHOWING) return;
        this.logState('startRound');
        
        this.state = this.STATES.SHOWING;
        this.action.innerHTML = '';
        this.playerIndex = 0; // CRITICAL FIX: Reset player pointer
        this.sequence.push(Math.floor(Math.random() * this.gridSize));
        
        const lvl = this.sequence.length;
        this.helper.innerHTML = `<span style="color:var(--lg-cyan);">WATCH PATTERN (LEVEL ${lvl})</span>`;
        
        const msg = document.getElementById('mf-msg');
        if (msg) {
            msg.innerText = `LEVEL ${lvl}`;
            msg.style.opacity = '0.1';
        }

        // Expand board
        if (lvl === 7 && this.gridSize === 4) {
            this.gridSize = 6;
            this.renderStage();
            this.safeTimeout(() => this.showSequence(), 800);
            return;
        }

        if (lvl > 4) {
            const grid = document.getElementById('mf-grid');
            if (grid) grid.style.transform = `rotate(${Math.random()*10 - 5}deg) scale(${0.9 + Math.random()*0.1})`;
        }

        this.safeTimeout(() => this.showSequence(), 600);
    }

    showSequence() {
        if (this.state === this.STATES.DEAD) return;
        this.logState('showSequence');
        
        const lvl = this.sequence.length;
        const flashDur = Math.max(100, 400 - (lvl * 15));
        const waitDur = Math.max(80, 250 - (lvl * 10));

        let step = 0;
        const loop = () => {
            if (this.state === this.STATES.DEAD) return;
            if (step >= this.sequence.length) {
                this.enablePlayerInput();
                return;
            }
            this.triggerVisualFlash(this.sequence[step], flashDur);
            step++;
            this.safeTimeout(loop, flashDur + waitDur);
        };
        loop();
    }

    enablePlayerInput() {
        this.logState('enablePlayerInput');
        this.state = this.STATES.INPUT;
        
        const grid = document.getElementById('mf-grid');
        if(grid) grid.style.transform = 'none'; // Un-tilt the board
        
        this.helper.innerHTML = `<span style="color:var(--lg-warning);">YOUR TURN: EXECUTE PATTERN</span>`;
    }

    triggerVisualFlash(idx, dur=300) {
        if (this.state === this.STATES.DEAD) return;
        const el = document.getElementById(`mf-${idx}`);
        if (!el) return;
        
        const color = el.dataset.color;
        el.style.background = `${color}44`;
        el.style.borderColor = color;
        el.style.boxShadow = `0 0 30px ${color}`;
        
        this.safeTimeout(() => {
            if (this.state === this.STATES.DEAD) return;
            el.style.background = 'rgba(255,255,255,0.03)';
            el.style.borderColor = 'rgba(255,255,255,0.1)';
            el.style.boxShadow = 'none';
        }, dur);
    }

    handlePlayerTap(idx) {
        if (this.state !== this.STATES.INPUT) return; // Strict lock
        
        vibrate(30);
        this.triggerVisualFlash(idx, 150);
        this.validateInput(idx);
    }

    validateInput(idx) {
        if (idx !== this.sequence[this.playerIndex]) {
            this.handleFailure();
            return;
        }

        // Correct tap
        this.playerIndex++;
        this.score += 20 * this.sequence.length;
        const scoreEl = document.getElementById('mf-score');
        if(scoreEl) scoreEl.innerText = this.score;

        if (this.playerIndex === this.sequence.length) {
            this.handleRoundSuccess();
        }
    }

    handleRoundSuccess() {
        this.logState('handleRoundSuccess');
        this.state = this.STATES.IDLE; // Lock inputs immediately
        
        this.api.addXP(this.sequence.length * 10);
        this.helper.innerHTML = `<span style="color:var(--lg-success);">PATTERN ACCEPTED</span>`;
        
        this.safeTimeout(() => this.startRound(), 800);
    }

    handleFailure() {
        this.logState('handleFailure');
        this.state = this.STATES.FAIL;
        
        vibrate([100, 50, 200]);
        this.api.saveScore(this.score);
        
        const lvl = this.sequence.length;
        this.helper.innerHTML = `<span style="color:var(--lg-danger);">BREACH DETECTED AT LEVEL ${lvl}</span>`;
        
        const bg = document.getElementById('mf-bg');
        if(bg) bg.style.background = 'rgba(255,0,0,0.1)';
        
        const grid = document.getElementById('mf-grid');
        if(grid) grid.style.transform = 'scale(0.9)';

        this.action.innerHTML = `
            <div style="display:flex; gap:12px; width:100%;">
                <button id="mf-retry-btn" class="btn-mobile-primary" style="background:var(--lg-danger);">RETRY SEQUENCE</button>
            </div>
        `;
        const retryBtn = document.getElementById('mf-retry-btn');
        if (retryBtn) retryBtn.onclick = () => this.resetRound();
    }

    resetRound() {
        if (this.state === this.STATES.DEAD) return;
        this.logState('resetRound');
        
        this.clearAllTimers(); // Kill all lingering animations
        this.state = this.STATES.IDLE;
        this.sequence = [];
        this.playerIndex = 0;
        this.score = 0;
        this.gridSize = 4;
        
        const bg = document.getElementById('mf-bg');
        if(bg) bg.style.background = 'transparent';
        
        const grid = document.getElementById('mf-grid');
        if(grid) grid.style.transform = 'none';

        this.renderStage();
        this.helper.innerHTML = `<span style="color:var(--lg-cyan);">SYSTEM REBOOTED.</span>`;
        
        // Fast start delay
        this.safeTimeout(() => this.startRound(), 500);
    }
};

// ── Game 5: Roast Battle (Card Swipe UX) ──
GameEngines['roast-battle'] = class {
    constructor(stage, helper, action, api) {
        this.stage = stage;
        this.helper = helper;
        this.action = action;
        this.api = api;
        this.destroyed = false;
        this.score = 0;
    }

    destroy() {
        this.destroyed = true;
    }

    start() {
        this.score = 0;
        this.nextRound();
    }

    generateRoast() {
        const d = window.GameData.roast;
        let template = d.templates[Math.floor(Math.random() * d.templates.length)];
        const matches = template.match(/\{([a-zA-Z_]+)\}/g);
        if (matches) {
            matches.forEach(m => {
                const key = m.replace(/[{}]/g, '');
                const words = d.vocab[key];
                if(words) template = template.replace(m, words[Math.floor(Math.random() * words.length)]);
            });
        }
        
        if (this.api.hasSeen(template)) return this.generateRoast();
        this.api.addToHistory(template);
        
        return template;
    }

    generateChoices() {
        const d = window.GameData.roast.comebacks;
        const correctPool = d.find(x => x.type === 'savage').text;
        const weakPool1 = d.find(x => x.type === 'nerd').text;
        const weakPool2 = d.find(x => x.type === 'brainrot').text;

        let choices = [
            { text: correctPool[Math.floor(Math.random() * correctPool.length)], isCorrect: true },
            { text: weakPool1[Math.floor(Math.random() * weakPool1.length)], isCorrect: false },
            { text: weakPool2[Math.floor(Math.random() * weakPool2.length)], isCorrect: false }
        ];
        choices.sort(() => Math.random() - 0.5);
        return choices;
    }

    nextRound() {
        if(this.destroyed) return;
        const attack = this.generateRoast();
        const choices = this.generateChoices();
        
        this.stage.innerHTML = `
            <div style="position:absolute; top:15px; right:15px; font-weight:bold; font-size:clamp(1rem, 3vw, 1.2rem); color:var(--lg-violet-bright);">Rep: ${this.score}</div>
            
            <div style="width:100%; max-width:400px; padding:clamp(1.5rem, 5vw, 2.5rem) 1.5rem; background:rgba(255,92,122,0.05); border:1px solid rgba(255,92,122,0.3); border-radius:20px; text-align:center; box-shadow:0 10px 40px rgba(255,92,122,0.1); position:relative;">
                <div style="position:absolute; top:-15px; left:50%; transform:translateX(-50%); background:#FF5C7A; color:#000; padding:4px 12px; border-radius:50px; font-size:0.75rem; font-weight:800; text-transform:uppercase;">Incoming Attack</div>
                <h3 style="font-family:'Syne',sans-serif; font-size:clamp(1.2rem, 5vw, 1.6rem); color:var(--lg-danger); margin:0; line-height:1.4;">"${attack}"</h3>
            </div>
        `;

        this.helper.innerText = "Select the best comeback.";
        
        this.action.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:10px; width:100%;">
                ${choices.map((c, i) => `
                    <button id="rb-choice-${i}" class="rb-choice touch-target" data-correct="${c.isCorrect}" style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:12px; color:var(--lg-text); text-align:left; padding:12px 16px; font-size:clamp(0.9rem, 3vw, 1rem); font-weight:600; line-height:1.3; cursor:pointer;">
                        ${c.text}
                    </button>
                `).join('')}
            </div>
        `;
        
        choices.forEach((c, i) => {
            const btn = document.getElementById(`rb-choice-${i}`);
            if (btn) btn.onclick = () => this.handleChoice(btn);
        });
    }

    handleChoice(btn) {
        if(this.destroyed) return;
        
        // Disable all
        document.querySelectorAll('.rb-choice').forEach(b => {
            b.onclick = null;
            b.style.opacity = '0.5';
        });
        
        btn.style.opacity = '1';
        btn.style.transform = 'scale(1.02)';
        const isCorrect = btn.dataset.correct === 'true';
        
        if (isCorrect) {
            vibrate(50);
            this.score += 150;
            this.api.addXP(30);
            this.helper.innerHTML = `<span style="color:var(--lg-success); font-weight:800;">CRITICAL! +150 Rep</span>`;
            btn.style.borderColor = 'var(--lg-success)';
            btn.style.background = 'rgba(46,232,184,0.1)';
        } else {
            vibrate([50, 100, 50]);
            this.score = Math.max(0, this.score - 100);
            this.helper.innerHTML = `<span style="color:var(--lg-danger); font-weight:800;">WEAK! -100 Rep</span>`;
            btn.style.borderColor = 'var(--lg-danger)';
            btn.style.background = 'rgba(255,92,122,0.1)';
        }
        
        this.api.saveScore(this.score);
        document.querySelector('.lg-violet-bright').innerText = `Rep: ${this.score}`;
        
        setTimeout(() => this.nextRound(), 2000);
    }
};
