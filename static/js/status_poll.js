/**
 * Status polling for thesis generation progress.
 * Polls /thesis/status/<id>/json/ every 3 seconds.
 */

const POLL_INTERVAL_MS = 3000;

const STEP_MAP = {
    'PENDING': 0,
    'processing': 1,
    'extracted': 2,
    'chunked': 3,
    'llm_done': 4,
    'pdf_rendered': 4,
    'PROCESSING': 1,
    'COMPLETED': 5,
    'FAILED': -1,
};

const STEP_IDS = [
    'step-uploading',
    'step-extracting',
    'step-analyzing',
    'step-generating',
    'step-creating',
];

const STATUS_LABELS = {
    'PENDING': 'Waiting to start...',
    'PROCESSING': 'Processing your document...',
    'processing': 'Processing your document...',
    'extracted': 'Text extracted, chunking...',
    'chunked': 'Analyzing content with AI...',
    'llm_done': 'Creating PDF document...',
    'pdf_rendered': 'Finalizing PDF...',
    'COMPLETED': 'Thesis generated successfully!',
    'FAILED': 'Generation failed.',
};

function updateSteps(activeIndex) {
    STEP_IDS.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('active', 'completed');
        if (i < activeIndex) {
            el.classList.add('completed');
            el.querySelector('.step-icon').innerHTML = '<i class="bi bi-check-lg"></i>';
        } else if (i === activeIndex) {
            el.classList.add('active');
        }
    });
}

function updateUI(data) {
    const progress = data.progress_percentage || 0;
    const status = data.status;

    // Update progress bar
    const bar = document.getElementById('progressBar');
    if (bar) {
        bar.style.width = progress + '%';
        bar.setAttribute('aria-valuenow', progress);
    }

    // Update percentage text
    const pct = document.getElementById('progressPercent');
    if (pct) pct.textContent = progress + '%';

    // Update status text
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = STATUS_LABELS[status] || 'Processing...';
    }

    // Update step indicators
    const stepIndex = STEP_MAP[status] !== undefined ? STEP_MAP[status] : 0;
    if (stepIndex >= 0) updateSteps(stepIndex);

    // Show completed actions
    if (status === 'COMPLETED') {
        document.getElementById('completedActions')?.classList.remove('d-none');
        document.getElementById('progressBar')?.classList.remove('progress-bar-animated');
        document.getElementById('progressBar')?.classList.add('bg-success');
        document.getElementById('progressBar')?.classList.remove('bg-primary');
        updateSteps(STEP_IDS.length); // all completed
    }

    // Show failed state
    if (status === 'FAILED') {
        document.getElementById('failedState')?.classList.remove('d-none');
        document.getElementById('progressBar')?.classList.remove('progress-bar-animated');
        document.getElementById('progressBar')?.classList.add('bg-danger');
        document.getElementById('progressBar')?.classList.remove('bg-primary');
        if (data.error_message) {
            const errEl = document.getElementById('errorMessage');
            if (errEl) errEl.textContent = data.error_message;
        }
    }
}

function startPolling(thesisId, initialStatus) {
    // If already completed/failed on page load, show final state immediately
    if (initialStatus === 'COMPLETED' || initialStatus === 'FAILED') {
        fetch(`/thesis/status/${thesisId}/json/`)
            .then(r => r.json())
            .then(data => updateUI(data))
            .catch(console.error);
        return;
    }

    const intervalId = setInterval(async () => {
        try {
            const resp = await fetch(`/thesis/status/${thesisId}/json/`);
            if (!resp.ok) {
                console.error('Status poll failed:', resp.status);
                return;
            }
            const data = await resp.json();
            updateUI(data);
            if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                clearInterval(intervalId);
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, POLL_INTERVAL_MS);
}
