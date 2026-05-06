/**
 * LamGen Zero-Maintenance WebRTC P2P Manager
 * Uses browser-to-browser DataChannels with lightweight HTTP signaling.
 * Optimized for zero server configuration and maximum reliability.
 */
class RTCManager {
    constructor() {
        this.peerConnection = null;
        this.dataChannel = null;
        this.roomCode = null;
        this.isHost = false;
        this.onMessage = null;
        this.onStatusChange = null;
        
        this.config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' }
            ],
            iceCandidatePoolSize: 10
        };
        
        this.pollInterval = null;
        this.connectionState = 'new';
    }

    async createRoom() {
        this.isHost = true;
        const res = await fetch('/games/api/rtc/create/', { method: 'POST' });
        const data = await res.json();
        this.roomCode = data.code;
        
        this.setupPeer();
        this.dataChannel = this.peerConnection.createDataChannel('gameData', {
            ordered: true
        });
        this.bindDataChannelEvents(this.dataChannel);
        
        const offer = await this.peerConnection.createOffer();
        await this.peerConnection.setLocalDescription(offer);
        
        // Wait for ICE gathering to complete before posting offer
        await this.waitForIceGathering();
        
        await this.postSignal({ offer: JSON.stringify(this.peerConnection.localDescription) });
        this.startPolling();
        
        return this.roomCode;
    }

    async joinRoom(code) {
        this.isHost = false;
        this.roomCode = code;
        this.setupPeer();
        
        this.peerConnection.ondatachannel = (event) => {
            this.dataChannel = event.channel;
            this.bindDataChannelEvents(this.dataChannel);
        };
        
        this.startPolling();
        return this.roomCode;
    }

    setupPeer() {
        if (this.peerConnection) this.peerConnection.close();
        this.peerConnection = new RTCPeerConnection(this.config);
        
        this.peerConnection.onconnectionstatechange = () => {
            this.connectionState = this.peerConnection.connectionState;
            if (this.onStatusChange) this.onStatusChange(this.connectionState);
            if (this.connectionState === 'connected') {
                this.stopPolling();
            }
        };
    }

    waitForIceGathering() {
        return new Promise((resolve) => {
            if (this.peerConnection.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (this.peerConnection.iceGatheringState === 'complete') {
                        this.peerConnection.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                this.peerConnection.addEventListener('icegatheringstatechange', checkState);
                // Fail-safe: resolve after 3 seconds anyway
                setTimeout(resolve, 3000);
            }
        });
    }

    bindDataChannelEvents(channel) {
        channel.onopen = () => {
            this.connectionState = 'connected';
            if (this.onStatusChange) this.onStatusChange('connected');
        };
        channel.onmessage = (event) => {
            if (this.onMessage) this.onMessage(JSON.parse(event.data));
        };
        channel.onclose = () => {
            this.connectionState = 'disconnected';
            if (this.onStatusChange) this.onStatusChange('disconnected');
        };
        channel.onerror = () => {
            this.connectionState = 'failed';
            if (this.onStatusChange) this.onStatusChange('failed');
        };
    }

    startPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        this.pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/games/api/rtc/get/${this.roomCode}/`);
                if (!res.ok) return;
                const data = await res.json();
                
                if (this.isHost) {
                    if (data.answer && !this.peerConnection.remoteDescription) {
                        const answer = new RTCSessionDescription(JSON.parse(data.answer));
                        await this.peerConnection.setRemoteDescription(answer);
                    }
                } else {
                    if (data.offer && !this.peerConnection.remoteDescription) {
                        const offer = new RTCSessionDescription(JSON.parse(data.offer));
                        await this.peerConnection.setRemoteDescription(offer);
                        const answer = await this.peerConnection.createAnswer();
                        await this.peerConnection.setLocalDescription(answer);
                        
                        await this.waitForIceGathering();
                        await this.postSignal({ answer: JSON.stringify(this.peerConnection.localDescription) });
                    }
                }
            } catch(e) {
                console.warn('Signaling poll failed', e);
            }
        }, 2000);
    }

    stopPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);
        this.pollInterval = null;
    }

    async postSignal(payload) {
        try {
            await fetch(`/games/api/rtc/post/${this.roomCode}/`, {
                method: 'POST',
                body: JSON.stringify(payload),
                headers: { 'Content-Type': 'application/json' }
            });
        } catch(e) {}
    }

    send(action, payload) {
        if (this.dataChannel && this.dataChannel.readyState === 'open') {
            try {
                this.dataChannel.send(JSON.stringify({ action, payload }));
            } catch(e) {
                console.error('P2P Send Error', e);
            }
        }
    }

    retry() {
        this.stopPolling();
        if (this.isHost) {
            this.createRoom();
        } else {
            this.joinRoom(this.roomCode);
        }
    }

    destroy() {
        this.stopPolling();
        if (this.dataChannel) this.dataChannel.close();
        if (this.peerConnection) this.peerConnection.close();
    }
}
