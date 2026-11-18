// ===== Tauri API =====
const { invoke } = window.__TAURI__.tauri;
const { listen } = window.__TAURI__.event;
const { appWindow } = window.__TAURI__.window;

// ===== State =====
let videoInfo = null;
let selectedQuality = null;
let selectedFormat = 'video';
let isDownloading = false;
let infoRequestSequence = 0;
let config = {
    apiKey: '',
    defaultPath: 'downloads',
    defaultQuality: '1080p'
};

// ===== DOM Elements =====
const urlInput = document.getElementById('urlInput');
const pasteBtn = document.getElementById('pasteBtn');
const getInfoBtn = document.getElementById('getInfoBtn');
const videoInfoSection = document.getElementById('videoInfoSection');
const videoThumbnail = document.getElementById('videoThumbnail');
const videoDuration = document.getElementById('videoDuration');
const videoTitle = document.getElementById('videoTitle');
const videoUploader = document.getElementById('videoUploader');
const videoViews = document.getElementById('videoViews');
const qualityGrid = document.getElementById('qualityGrid');
const savePathInput = document.getElementById('savePathInput');
const browseBtn = document.getElementById('browseBtn');
const downloadBtn = document.getElementById('downloadBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressPercent = document.getElementById('progressPercent');
const downloadSpeed = document.getElementById('downloadSpeed');
const timeRemaining = document.getElementById('timeRemaining');
const fileSize = document.getElementById('fileSize');
const cancelBtn = document.getElementById('cancelBtn');
const successSection = document.getElementById('successSection');
const successMessage = document.getElementById('successMessage');
const newDownloadBtn = document.getElementById('newDownloadBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const apiKeyInput = document.getElementById('apiKeyInput');
const defaultPathInput = document.getElementById('defaultPathInput');
const defaultQualitySelect = document.getElementById('defaultQualitySelect');
const browseDefaultBtn = document.getElementById('browseDefaultBtn');
const closeSettingsModal = document.getElementById('closeSettingsModal');
const cancelSettings = document.getElementById('cancelSettings');
const saveSettings = document.getElementById('saveSettings');
const loadingOverlay = document.getElementById('loadingOverlay');
const formatTabs = document.querySelectorAll('.format-tab');

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    setupEventListeners();
    setupProgressListener();
});

// ===== Event Listeners =====
function setupEventListeners() {
    // Paste button
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            urlInput.value = text;
            infoRequestSequence += 1;
            videoInfo = null;
            selectedQuality = null;
            videoInfoSection.style.display = 'none';
            showLoading(false);
            getInfoBtn.disabled = false;
            urlInput.focus();
        } catch (err) {
            console.error('Failed to read clipboard:', err);
        }
    });

    urlInput.addEventListener('input', () => {
        infoRequestSequence += 1;
        videoInfo = null;
        selectedQuality = null;
        videoInfoSection.style.display = 'none';
        showLoading(false);
        getInfoBtn.disabled = false;
    });

    // Get info button
    getInfoBtn.addEventListener('click', handleGetInfo);

    // URL input enter key
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleGetInfo();
        }
    });

    // Format tabs
    formatTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            formatTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            selectedFormat = tab.dataset.format;
            renderQualityOptions();
        });
    });

    // Browse button
    browseBtn.addEventListener('click', handleBrowseFolder);

    // Download button
    downloadBtn.addEventListener('click', handleDownload);

    // Cancel button
    cancelBtn.addEventListener('click', handleCancel);

    // New download button
    newDownloadBtn.addEventListener('click', resetUI);

    // Settings
    settingsBtn.addEventListener('click', () => {
        apiKeyInput.value = config.apiKey || '';
        defaultPathInput.value = config.defaultPath || 'downloads';
        defaultQualitySelect.value = config.defaultQuality || '1080p';
        settingsModal.classList.add('active');
    });
    browseDefaultBtn.addEventListener('click', async () => {
        try {
            const folder = await invoke('select_folder');
            if (folder) defaultPathInput.value = folder;
        } catch (err) {
            console.error('Failed to select default folder:', err);
        }
    });
    closeSettingsModal.addEventListener('click', () => settingsModal.classList.remove('active'));
    cancelSettings.addEventListener('click', () => settingsModal.classList.remove('active'));
    saveSettings.addEventListener('click', handleSaveSettings);

    // Close modal on outside click
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.remove('active');
        }
    });
}

// ===== Progress Listener =====
async function setupProgressListener() {
    await listen('download-progress', (event) => {
        try {
            const data = JSON.parse(event.payload);
            
            if (data.type === 'progress') {
                updateProgress(data);
            } else if (data.type === 'finished') {
                console.log('Download finished:', data.filename);
            } else if (data.type === 'complete') {
                handleDownloadComplete(data);
            } else if (data.type === 'error') {
                // The invoke promise reports the process exit as a rejection.
                // Do not show a second alert for the same failure event.
                console.error('Downloader process error:', data.error);
            }
        } catch (err) {
            console.error('Failed to parse progress:', err);
        }
    });
}

// ===== Config =====
function loadConfig() {
    try {
        const saved = localStorage.getItem('downloader_config');
        if (saved) {
            config = { ...config, ...JSON.parse(saved) };
        }
        // Migrate the old developer-machine default instead of exposing a dead path.
        if (/^C:\\Users\\Smixr\\/i.test(config.defaultPath || '')) {
            config.defaultPath = 'downloads';
            localStorage.setItem('downloader_config', JSON.stringify(config));
        }
        savePathInput.value = config.defaultPath || 'downloads';
        if (apiKeyInput) apiKeyInput.value = config.apiKey || '';
        if (defaultPathInput) defaultPathInput.value = config.defaultPath || 'downloads';
        if (defaultQualitySelect) defaultQualitySelect.value = config.defaultQuality || '1080p';
    } catch (err) {
        console.error('Failed to load config:', err);
    }
}

function handleSaveSettings() {
    config.apiKey = apiKeyInput.value;
    config.defaultPath = defaultPathInput.value || config.defaultPath;
    config.defaultQuality = defaultQualitySelect.value;

    localStorage.setItem('downloader_config', JSON.stringify(config));
    savePathInput.value = config.defaultPath;
    settingsModal.classList.remove('active');
}

// ===== Get Video Info =====
async function handleGetInfo() {
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }

    const normalizedUrl = normalizeYouTubeUrl(url);
    if (!normalizedUrl) {
        alert('Please enter a valid YouTube URL (HTTP(S), youtube.com or youtu.be)');
        return;
    }
    urlInput.value = normalizedUrl;
    const requestId = ++infoRequestSequence;

    showLoading(true);
    getInfoBtn.disabled = true;

    try {
        const result = await invoke('get_video_info', { url: normalizedUrl });
        if (requestId !== infoRequestSequence) return;
        videoInfo = JSON.parse(result);
        
        if (videoInfo.error) {
            throw new Error(videoInfo.error);
        }

        displayVideoInfo(videoInfo);
        videoInfoSection.style.display = 'block';
    } catch (err) {
        if (requestId === infoRequestSequence) {
            console.error('Failed to get video info:', err);
            alert('Failed to get video info: ' + err.message);
        }
    } finally {
        if (requestId === infoRequestSequence) {
            showLoading(false);
            getInfoBtn.disabled = false;
        }
    }
}

function displayVideoInfo(info) {
    // Thumbnail
    videoThumbnail.src = info.thumbnail || '';
    videoDuration.textContent = info.duration ? formatDuration(info.duration) : '0:00';

    // Duration

    // Title
    videoTitle.textContent = info.title || 'Unknown Title';

    // Uploader
    videoUploader.textContent = info.uploader || 'Unknown Channel';

    // Views
    videoViews.textContent = info.view_count ? formatViews(info.view_count) + ' views' : '0 views';

    // Render quality options
    renderQualityOptions();
}

function renderQualityOptions() {
    qualityGrid.innerHTML = '';

    if (selectedFormat === 'audio') {
        // Audio options
        const audioOptions = [
            { label: 'MP3 320kbps', value: 'audio', badge: 'BEST' }
        ];

        audioOptions.forEach(opt => {
            const option = createQualityOption(opt.label, opt.value, opt.badge);
            qualityGrid.appendChild(option);
        });

        // Select first by default
        const firstOption = qualityGrid.querySelector('.quality-option');
        if (firstOption) {
            firstOption.classList.add('selected');
            selectedQuality = 'audio';
        }
    } else {
        // Video options
        if (!videoInfo || !videoInfo.formats) return;

        const formats = videoInfo.formats;
        
        // Add "Best Quality" option
        const bestOption = createQualityOption('Best', 'best', 'MAX');
        qualityGrid.appendChild(bestOption);

        // Add specific quality options
        formats.forEach(format => {
            if (format.height) {
                const label = format.height + 'p';
                const value = format.height + 'p';
                let badge = '';
                
                if (format.height >= 2160) badge = '4K';
                else if (format.height >= 1440) badge = '2K';
                else if (format.height >= 1080) badge = 'FHD';
                else if (format.height >= 720) badge = 'HD';

                const option = createQualityOption(label, value, badge);
                qualityGrid.appendChild(option);
            }
        });

        // Select default quality
        const defaultOption = qualityGrid.querySelector(`[data-quality="${config.defaultQuality}"]`);
        if (defaultOption) {
            defaultOption.classList.add('selected');
            selectedQuality = config.defaultQuality;
        } else {
            // Select best available
            const firstOption = qualityGrid.querySelector('.quality-option');
            if (firstOption) {
                firstOption.classList.add('selected');
                selectedQuality = firstOption.dataset.quality;
            }
        }
    }

    // Add click handlers
    qualityGrid.querySelectorAll('.quality-option').forEach(option => {
        option.addEventListener('click', () => {
            qualityGrid.querySelectorAll('.quality-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            selectedQuality = option.dataset.quality;
        });
    });
}

function createQualityOption(label, value, badge) {
    const option = document.createElement('div');
    option.className = 'quality-option';
    option.dataset.quality = value;

    let badgeHtml = '';
    if (badge) {
        let badgeClass = '';
        if (badge === 'HD') badgeClass = 'hd';
        else if (badge === 'FHD') badgeClass = 'fhd';
        else if (badge === '4K' || badge === '2K' || badge === 'MAX') badgeClass = 'uhd';
        
        badgeHtml = `<div class="quality-badge ${badgeClass}">${badge}</div>`;
    }

    option.innerHTML = `
        <div class="quality-label">${label}</div>
        ${badgeHtml}
    `;

    return option;
}

// ===== Browse Folder =====
async function handleBrowseFolder() {
    try {
        const folder = await invoke('select_folder');
        if (folder) {
            savePathInput.value = folder;
        }
    } catch (err) {
        console.error('Failed to select folder:', err);
    }
}

// ===== Download =====
async function handleDownload() {
    if (!videoInfo || !selectedQuality) {
        alert('Please select a quality');
        return;
    }

    const savePath = savePathInput.value.trim();
    if (!savePath) {
        alert('Please select a save folder');
        return;
    }

    isDownloading = true;
    videoInfoSection.style.display = 'none';
    progressSection.style.display = 'block';
    downloadBtn.disabled = true;

    try {
        await invoke('start_download', {
            url: urlInput.value.trim(),
            quality: selectedQuality,
            formatType: selectedFormat,
            savePath: savePath
        });
    } catch (err) {
        console.error('Download failed:', err);
        handleDownloadError(err);
    }
}

function updateProgress(data) {
    const progress = data.progress || 0;
    progressFill.style.width = progress + '%';
    progressPercent.textContent = Math.round(progress) + '%';

    // Speed
    if (data.speed) {
        downloadSpeed.textContent = formatBytes(data.speed) + '/s';
    }

    // ETA
    if (data.eta) {
        timeRemaining.textContent = formatDuration(data.eta);
    }

    // File size
    if (data.downloaded && data.total) {
        fileSize.textContent = formatBytes(data.downloaded) + ' / ' + formatBytes(data.total);
    }
}

function handleDownloadComplete(data) {
    isDownloading = false;
    progressSection.style.display = 'none';
    successSection.style.display = 'block';
    successMessage.textContent = `"${data.title}" successfully downloaded!`;
}

function handleDownloadError(error) {
    isDownloading = false;
    progressSection.style.display = 'none';
    videoInfoSection.style.display = 'block';
    downloadBtn.disabled = false;
    alert('Download failed: ' + error);
}

async function handleCancel() {
    try {
        await invoke('cancel_download');
        isDownloading = false;
        progressSection.style.display = 'none';
        videoInfoSection.style.display = 'block';
        downloadBtn.disabled = false;
    } catch (err) {
        console.error('Failed to cancel:', err);
    }
}

// ===== Reset UI =====
function resetUI() {
    urlInput.value = '';
    videoInfo = null;
    selectedQuality = null;
    isDownloading = false;
    
    videoInfoSection.style.display = 'none';
    progressSection.style.display = 'none';
    successSection.style.display = 'none';
    
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';
    downloadSpeed.textContent = '0 MB/s';
    timeRemaining.textContent = '--:--';
    fileSize.textContent = '0 MB / 0 MB';
    
    downloadBtn.disabled = false;
    urlInput.focus();
}

// ===== Utility Functions =====
function normalizeYouTubeUrl(value) {
    try {
        const raw = value.trim();
        if (!raw || raw.startsWith('//')) return null;
        const candidate = /^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : 'https://' + raw;
        const parsed = new URL(candidate);
        if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) return null;
        if (parsed.port && !['80', '443'].includes(parsed.port)) return null;
        const host = parsed.hostname.toLowerCase().replace(/\.$/, '');
        if (!['youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','youtu.be','www.youtu.be'].includes(host)) return null;
        let id = '';
        if (host.endsWith('youtu.be')) id = parsed.pathname.split('/').filter(Boolean)[0] || '';
        else if (parsed.pathname === '/watch') id = parsed.searchParams.get('v') || '';
        else { const p = parsed.pathname.split('/').filter(Boolean); if (p.length === 2 && ['embed','shorts','live','v'].includes(p[0])) id = p[1]; }
        if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return null;
        parsed.hash = '';
        return parsed.toString();
    } catch (_) { return null; }
}

function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatViews(views) {
    if (views >= 1000000000) {
        return (views / 1000000000).toFixed(1) + 'B';
    }
    if (views >= 1000000) {
        return (views / 1000000).toFixed(1) + 'M';
    }
    if (views >= 1000) {
        return (views / 1000).toFixed(1) + 'K';
    }
    return views.toString();
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}
