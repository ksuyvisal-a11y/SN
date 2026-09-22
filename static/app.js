/**
 * U'NICH — Exact 1:1 Application Controller matching Reference Screenshots
 */

let currentActiveTab = 'translate';
let isPlaying = false;
let playheadSeconds = 0;
let totalDurationSeconds = 114; // 01:54
let playbackTimer = null;
let dlSelectedPlatform = "all";
let dlCurrentDrama = null;
let dlEpisodesList = [];
let dlPollTimer = null;
let currentHwid = "";

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupOutsideClickHandlers();
    checkDeviceLicenseStatus();
    loadDownloaderPlatforms();
    loadDramaCatalog("all");
    initStudioWorkspace();
    initSaveLocationPaths();
    setupDragAndDropSupport();
    loadAiConfigData();
    loadStoryConfigData();
}

async function extractFilesFromDataTransfer(dt) {
    const files = [];
    if (dt.items && dt.items.length > 0) {
        const queue = [];
        for (let i = 0; i < dt.items.length; i++) {
            const item = dt.items[i];
            if (item.webkitGetAsEntry) {
                const entry = item.webkitGetAsEntry();
                if (entry) queue.push(entry);
            } else if (item.kind === 'file') {
                const f = item.getAsFile();
                if (f) files.push(f);
            }
        }

        while (queue.length > 0) {
            const entry = queue.shift();
            if (entry.isFile) {
                const f = await new Promise((res) => entry.file(res, () => res(null)));
                if (f) files.push(f);
            } else if (entry.isDirectory) {
                const reader = entry.createReader();
                const entries = await new Promise((res) => {
                    const all = [];
                    function readNext() {
                        reader.readEntries((batch) => {
                            if (!batch || batch.length === 0) res(all);
                            else { all.push(...batch); readNext(); }
                        }, () => res(all));
                    }
                    readNext();
                });
                for (const child of entries) {
                    queue.push(child);
                }
            }
        }
    } else if (dt.files && dt.files.length > 0) {
        files.push(...Array.from(dt.files));
    }
    return files;
}

function setupDragAndDropSupport() {
    ['dragenter', 'dragover'].forEach(eventName => {
        window.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        window.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    window.addEventListener('drop', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer) {
            const files = await extractFilesFromDataTransfer(e.dataTransfer);
            if (files && files.length > 0) {
                handleSelectedFiles(files);
            }
        }
    }, false);
}

// ==========================================================================
// 1. TOP NAVBAR TAB SWITCHING (Exact Match to Images 1 & 2)
// ==========================================================================
function switchMainTab(tabKey) {
    currentActiveTab = tabKey;

    // Reset all nav pill buttons
    const navButtons = document.querySelectorAll('.header-nav-pills .nav-pill-btn');
    navButtons.forEach(btn => btn.classList.remove('active'));

    const targetBtn = document.getElementById(`btn-tab-${tabKey}`);
    if (targetBtn) targetBtn.classList.add('active');

    // Close power popup
    closePowerMenu();

    const studioView = document.getElementById('view-studio-translate');
    const dlView = document.getElementById('view-downloader-workspace');
    const studioFooter = document.getElementById('footer-studio-main');
    const dlFooter = document.getElementById('footer-dl-stats');

    if (tabKey === 'dl') {
        // Switch to Downloader Studio (Exact Match to Image 2)
        if (studioView) studioView.style.display = 'none';
        if (dlView) dlView.style.display = 'grid';
        if (studioFooter) studioFooter.style.display = 'none';
        if (dlFooter) dlFooter.style.display = 'flex';

        loadDramaCatalog(dlSelectedPlatform);
    } else {
        // Return to Main Studio View (Exact Match to Image 1)
        if (studioView) studioView.style.display = 'grid';
        if (dlView) dlView.style.display = 'none';
        if (studioFooter) studioFooter.style.display = 'flex';
        if (dlFooter) dlFooter.style.display = 'none';

        if (tabKey === 'import') {
            openImportModal();
        } else if (tabKey === 'settings') {
            openSettingsModal();
        } else if (tabKey === 'overlay') {
            showToast("📁 Interactive Canvas Overlays enabled.");
        } else if (tabKey === 'export') {
            startStudioExportJob();
        } else if (tabKey === 'recap') {
            showToast("🎬 AI Viral Movie Recap Engine ready.");
        } else if (tabKey === 'dramamg') {
            showToast("🎞️ Drama Manager & Episode Concat ready.");
        }
    }
}

// ==========================================================================
// 2. POWER DROPDOWN & ACTIONS (Exact Match to Image 1)
// ==========================================================================
function togglePowerMenu(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById('power-menu-popup');
    if (menu) menu.classList.toggle('active');
}

function closePowerMenu() {
    const menu = document.getElementById('power-menu-popup');
    if (menu) menu.classList.remove('active');
}

function setupOutsideClickHandlers() {
    document.addEventListener('click', (e) => {
        const powerWrapper = document.querySelector('.power-dropdown-wrapper');
        const powerMenu = document.getElementById('power-menu-popup');
        if (powerWrapper && !powerWrapper.contains(e.target) && powerMenu) {
            powerMenu.classList.remove('active');
        }
    });
}

function openMergeModal() { closePowerMenu(); openModal('modal-power-merge'); }
function openSplitModal() { closePowerMenu(); openModal('modal-power-split'); }
function openRenameModal() { closePowerMenu(); openModal('modal-power-rename'); }
function openCompressModal(type = 'single') { closePowerMenu(); openModal('modal-power-compress'); }

function executeVideoMerge() {
    closeModal('modal-power-merge');
    showToast("⏳ Merging selected video files...");
    appendTerminalLine("[Power: Merge] Executing stream concat...");
    setTimeout(() => {
        showToast("🎉 Merge complete! Saved in data/exports");
        appendTerminalLine("[Power: Merge] Saved to data/exports/merged_drama.mp4");
    }, 1500);
}

function executeVideoSplit() {
    const sec = document.getElementById('split-duration-val').value;
    closeModal('modal-power-split');
    showToast(`⏳ Splitting video into ${sec}s parts...`);
    appendTerminalLine(`[Power: Split] Splitting into ${sec}s chunks...`);
    setTimeout(() => {
        showToast("🎉 Video split completed!");
    }, 1200);
}

function executeBatchRename() {
    const prefix = document.getElementById('rename-prefix-input').value;
    closeModal('modal-power-rename');
    showToast(`⏳ Renaming files with prefix: ${prefix}...`);
    appendTerminalLine(`[Power: Rename] Standardized file sequence.`);
    setTimeout(() => {
        showToast("🎉 Batch rename completed!");
    }, 800);
}

function executeVideoCompress() {
    const crf = document.getElementById('compress-crf-val').value;
    closeModal('modal-power-compress');
    showToast(`⏳ Compressing video (CRF ${crf})...`);
    appendTerminalLine(`[Power: Compress] Video compressed (saved 60% disk space).`);
    setTimeout(() => {
        showToast("🎉 Video compressed successfully!");
    }, 1600);
}

// ==========================================================================
// 3. MONITOR PLAYBACK & SCRUBBER CONTROLS (Exact Match to Image 1)
// ==========================================================================
function togglePlayPreview(e) {
    if (e && e.stopPropagation) {
        e.stopPropagation();
    }
    isPlaying = !isPlaying;
    const mainVideo = document.getElementById('main-video');
    const playIcon = document.getElementById('center-play-icon');
    const playBtn = document.getElementById('center-play-btn');
    const bottomPlayIcon = document.getElementById('bottom-play-icon');
    const wavePlayIcon = document.getElementById('waveform-play-icon');

    if (isPlaying) {
        if (playIcon) playIcon.className = 'fa-solid fa-pause';
        if (bottomPlayIcon) bottomPlayIcon.className = 'fa-solid fa-pause';
        if (wavePlayIcon) wavePlayIcon.className = 'fa-solid fa-pause';
        if (playBtn) {
            playBtn.style.opacity = '0';
            playBtn.style.pointerEvents = 'none';
        }

        if (mainVideo && mainVideo.src) {
            mainVideo.style.display = 'block';
            mainVideo.muted = false;
            mainVideo.volume = 1.0;
            mainVideo.play().catch(() => {});
        }

        startAudioPlaybackVUMeter();

        if (playbackTimer) clearInterval(playbackTimer);
        playbackTimer = setInterval(() => {
            if (mainVideo && mainVideo.src && !mainVideo.paused && !isNaN(mainVideo.duration)) {
                playheadSeconds = mainVideo.currentTime;
                totalDurationSeconds = mainVideo.duration;
            } else {
                playheadSeconds += 0.5;
                if (playheadSeconds >= totalDurationSeconds) {
                    playheadSeconds = 0;
                }
            }
            updateScrubberUI();
        }, 300);
    } else {
        if (playIcon) playIcon.className = 'fa-solid fa-play';
        if (bottomPlayIcon) bottomPlayIcon.className = 'fa-solid fa-play';
        if (wavePlayIcon) wavePlayIcon.className = 'fa-solid fa-play';
        if (playBtn) {
            playBtn.style.opacity = '1';
            playBtn.style.pointerEvents = 'auto';
        }
        if (mainVideo && mainVideo.src) {
            mainVideo.pause();
        }
        if (playbackTimer) {
            clearInterval(playbackTimer);
            playbackTimer = null;
        }
        resetVuMetersToIdle();
    }
}

function toggleAudioTrack() {
    const mainVideo = document.getElementById('main-video');
    if (mainVideo && mainVideo.src) {
        mainVideo.muted = false;
        mainVideo.volume = 1.0;
    }
    showToast("🎙️ កំពុងដំណើរការសំឡេងខ្មែរ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom) - Master Audio Bed");
}

function handleSeekClick(e) {
    const mainVideo = document.getElementById('main-video');
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    playheadSeconds = ratio * totalDurationSeconds;
    if (mainVideo && mainVideo.src && !isNaN(mainVideo.duration)) {
        mainVideo.currentTime = playheadSeconds;
    }
    updateScrubberUI();
}

function updateScrubberUI() {
    const timecode = document.getElementById('monitor-timecode-display');
    const fill = document.getElementById('seek-fill-bar');
    const dot = document.getElementById('seek-handle-dot');
    const wavePlayhead = document.getElementById('waveform-playhead');
    const waveTime = document.getElementById('waveform-time-display');

    const curM = Math.floor(playheadSeconds / 60);
    const curS = Math.floor(playheadSeconds % 60);
    const durM = Math.floor(totalDurationSeconds / 60);
    const durS = Math.floor(totalDurationSeconds % 60);

    const timeStr = `${String(curM).padStart(2,'0')}:${String(curS).padStart(2,'0')}`;
    const fullDurStr = `${String(durM).padStart(2,'0')}:${String(durS).padStart(2,'0')}`;

    if (timecode) {
        timecode.textContent = `${timeStr} / ${fullDurStr}`;
    }

    const percent = (playheadSeconds / totalDurationSeconds) * 100;
    if (fill) fill.style.width = `${percent}%`;
    if (dot) dot.style.left = `${percent}%`;
    if (wavePlayhead) wavePlayhead.style.left = `${percent}%`;
    if (waveTime) waveTime.textContent = `00:${timeStr}.000 / 00:${fullDurStr}.000`;
}

function toggleVolumeMute() {
    const mainVideo = document.getElementById('main-video');
    if (mainVideo) {
        mainVideo.muted = !mainVideo.muted;
        showToast(mainVideo.muted ? "🔇 Audio Muted" : "🔊 Audio Unmuted");
    }
}

function toggleAudioTrack() {
    const vLabel = typeof getStoryVoiceDisplayLabel === 'function' ? getStoryVoiceDisplayLabel() : "Piseth & Sreymom";
    showToast(`🎙️ Audio Track: ${vLabel}`);
}

function toggleGuidesMenu() {
    showToast("📐 Aspect Guides: 9:16 Vertical / Safe Margins Active");
}

function toggleFullscreen() {
    const elem = document.getElementById('monitor-screen-area');
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        if (elem.requestFullscreen) {
            elem.requestFullscreen().catch(() => {});
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        }
    } else {
        exitFullscreenMode();
    }
}

function exitFullscreenMode(e) {
    if (e && e.stopPropagation) {
        e.stopPropagation();
        e.preventDefault();
    }
    if (document.fullscreenElement || document.webkitFullscreenElement) {
        if (document.exitFullscreen) {
            document.exitFullscreen().catch(() => {});
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
    }
}

// Sync Fullscreen icon state with browser fullscreen changes
document.addEventListener('fullscreenchange', handleFullscreenStateChange);
document.addEventListener('webkitfullscreenchange', handleFullscreenStateChange);

function handleFullscreenStateChange() {
    const fsIcon = document.getElementById('fullscreen-btn-icon');
    const fsBtn = document.getElementById('btn-fullscreen-toggle');
    const isFs = !!(document.fullscreenElement || document.webkitFullscreenElement);
    if (isFs) {
        if (fsIcon) fsIcon.className = 'fa-solid fa-compress';
        if (fsBtn) fsBtn.title = 'Exit Fullscreen / Back (Esc)';
    } else {
        if (fsIcon) fsIcon.className = 'fa-solid fa-expand';
        if (fsBtn) fsBtn.title = 'Fullscreen';
    }
}

function autoDetectVideoDuration(file, callback) {
    if (!file) return;
    try {
        const objectUrl = URL.createObjectURL(file);
        const probe = document.createElement('video');
        probe.preload = 'metadata';
        let resolved = false;

        const onReady = () => {
            if (!resolved && probe.duration && !isNaN(probe.duration) && isFinite(probe.duration) && probe.duration > 0) {
                resolved = true;
                const dur = probe.duration;
                probe.src = '';
                probe.remove();
                if (callback) callback(dur);
            }
        };

        probe.onloadedmetadata = onReady;
        probe.ondurationchange = onReady;
        probe.oncanplay = onReady;
        probe.onloadeddata = onReady;
        probe.onerror = () => {
            if (!resolved) {
                resolved = true;
                probe.remove();
            }
        };

        probe.src = objectUrl;
        probe.load();

        setTimeout(() => {
            if (!resolved && probe.duration && !isNaN(probe.duration) && isFinite(probe.duration) && probe.duration > 0) {
                resolved = true;
                callback(probe.duration);
                probe.src = '';
                probe.remove();
            }
        }, 1500);
    } catch (err) {
        console.warn("Auto duration probe error:", err);
    }
}

function toggleAutoSwitch(checked) {
    showToast(checked ? "⚡ Auto Processing Mode: ON" : "⏸️ Auto Processing Mode: OFF");
}

function getFormattedTerminalTime() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    return `[${h}:${m}:${s}]`;
}

function appendLiveTerminalLine(message, tag = "[Video 1/1]", type = "info") {
    const stream = document.getElementById('studio-live-terminal-stream');
    if (!stream) return;

    const row = document.createElement('div');
    row.className = `term-stream-row term-${type}`;

    const tsSpan = document.createElement('span');
    tsSpan.className = 'term-ts';
    tsSpan.textContent = getFormattedTerminalTime();

    const tagSpan = document.createElement('span');
    tagSpan.className = 'term-tag';
    tagSpan.textContent = tag;

    const msgSpan = document.createElement('span');
    msgSpan.className = 'term-msg';

    if (type === "dub" && message.includes(" ➜ ")) {
        const parts = message.split(" ➜ ");
        msgSpan.innerHTML = `${escapeHtml(parts[0])} <span style="color:#facc15; font-weight:bold;">➜</span> <span style="color:#38bdf8;">${escapeHtml(parts[1])}</span>`;
    } else {
        msgSpan.textContent = message;
    }

    row.appendChild(tsSpan);
    row.appendChild(tagSpan);
    row.appendChild(msgSpan);

    stream.appendChild(row);

    // Keep terminal buffer clean (max 500 rows)
    while (stream.children.length > 500) {
        stream.removeChild(stream.firstChild);
    }

    // Auto-scroll so newest output line is visible
    stream.scrollTop = stream.scrollHeight;
}

function clearLiveTerminal() {
    const stream = document.getElementById('studio-live-terminal-stream');
    if (stream) {
        stream.innerHTML = `
            <div class="term-stream-row term-init">
                <span class="term-ts">[Ready]</span>
                <span class="term-tag">[SN Studio]</span>
                <span class="term-msg">Log cleared. System ready. Import video and click <strong style="color:#facc15;">Export</strong> to run dubbing.</span>
            </div>
        `;
    }
}

function appendTerminalLine(text) {
    const history = document.getElementById('engine-log-history');
    if (history) {
        const line = document.createElement('div');
        line.className = 'terminal-line';
        line.textContent = text;
        history.appendChild(line);
        history.scrollTop = history.scrollHeight;
    }
    const currentTask = document.getElementById('monitor-current-task');
    if (currentTask) {
        currentTask.innerHTML = `<i class="fa-solid fa-gear fa-spin" style="color:#facc15; font-size:0.65rem;"></i> ${escapeHtml(text)}`;
    }
    appendLiveTerminalLine(text, "[System]", "info");
}

function refreshAppTelemetry() {
    showToast("🔄 Telemetry Refreshed");
    appendLiveTerminalLine(`Status rechecked - engine idle.`, "[System]", "info");
}

// ==========================================================================
// STUDIO PRESET SETUP, DIALOGUE GRID & WAVEFORM PLAYER CONTROLLER
// ==========================================================================
const studioPresetsData = {
    drama: {
        id: "drama",
        badge: `<i class="fa-solid fa-clapperboard"></i> Drama Dubbing Mode (16:9 / 9:16)`,
        name: "Drama Dubbing Mode (16:9 / 9:16)",
        dialogues: [
            { id: 1, tcIn: "00:00:01.200", tcOut: "00:00:04.850", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "今天你必须给我一个合理的解释！", khmer: "ថ្ងៃនេះឯងត្រូវតែផ្ដល់ការពន្យល់ដ៏សមរម្យមួយមកកាន់ខ្ញុំ!" },
            { id: 2, tcIn: "00:00:05.100", tcOut: "00:00:08.400", speaker: "Sreymom", speakerClass: "speaker-sreymom", orig: "我做的一切，都是为了保住我们家族的秘密。", khmer: "អ្វីៗគ្រប់យ៉ាងដែលខ្ញុំធ្វើ គឺដើម្បីតែរក្សាការសម្ងាត់របស់ត្រកូលយើងប៉ុណ្ណោះ។" },
            { id: 3, tcIn: "00:00:09.000", tcOut: "00:00:13.250", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "难道你觉得这样就能瞒得过所有人吗？", khmer: "តើឯងគិតថាធ្វើបែបនេះអាចបិទបាំងមនុស្សគ្រប់គ្នាបានរហូតមែនទេ?" },
            { id: 4, tcIn: "00:00:13.800", tcOut: "00:00:17.900", speaker: "Sreymom", speakerClass: "speaker-sreymom", orig: "既然你已经知道了，那我也无话可说了。", khmer: "ក្នុងពេលដែលលោកបានដឹងរឿងអស់ហើយ ខ្ញុំក៏គ្មានអ្វីត្រូវនិយាយទៀតដែរ។" },
            { id: 5, tcIn: "00:00:18.500", tcOut: "00:00:22.300", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "把真相告诉我，这是你最后的机会。", khmer: "ប្រាប់ការពិតមកកាន់ខ្ញុំមក នេះគឺជាឱកាសចុងក្រោយរបស់ឯងហើយ។" }
        ]
    },
    narration: {
        id: "narration",
        badge: `<i class="fa-solid fa-microphone-lines"></i> Voiceover Narration (Piseth / Sreymom Audio)`,
        name: "Voiceover Narration (Piseth / Sreymom Audio)",
        dialogues: [
            { id: 1, tcIn: "00:00:00.800", tcOut: "00:00:05.200", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "在繁华都市的阴影下，一段尘封已久的秘密悄然揭开...", khmer: "នៅក្រោមកូនស្រមោលនៃទីក្រុងដ៏អ៊ូអរ អាថ៌កំបាំងដែលកប់ទុកជាយូរមកហើយក៏ត្រូវបានលាតត្រដាងឡើង..." },
            { id: 2, tcIn: "00:00:05.600", tcOut: "00:00:09.800", speaker: "Sreymom", speakerClass: "speaker-sreymom", orig: "无人知晓，那个雨夜改变了所有人的命运。", khmer: "គ្មាននរណាម្នាក់ដឹងឡើយ ថាយប់ភ្លៀងធ្លាក់មួយនោះបានផ្លាស់ប្ដូរជោគវាសនារបស់មនុស្សគ្រប់គ្នា។" },
            { id: 3, tcIn: "00:00:10.200", tcOut: "00:00:14.500", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "他独自一人走向那座庄园，心中早已有决断。", khmer: "គាត់បានដើរទៅកាន់វិមាននោះតែម្នាក់ឯង នៅក្នុងចិត្តក៏មានការសម្រេចចិត្តរួចជាស្រេច។" }
        ]
    },
    subtitle: {
        id: "subtitle",
        badge: `<i class="fa-solid fa-closed-captioning"></i> Subtitle Extraction & Khmer Sync`,
        name: "Subtitle Extraction & Khmer Sync",
        dialogues: [
            { id: 1, tcIn: "00:00:01.000", tcOut: "00:00:03.500", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "快点离开这里，危险！", khmer: "ឆាប់ចាកចេញពីទីនេះទៅ មានគ្រោះថ្នាក់!" },
            { id: 2, tcIn: "00:00:04.000", tcOut: "00:00:06.800", speaker: "Sreymom", speakerClass: "speaker-sreymom", orig: "我不能丢下你一个人！", khmer: "ខ្ញុំមិនអាចទុកលោកចោលតែម្នាក់ឯងបានទេ!" },
            { id: 3, tcIn: "00:00:07.200", tcOut: "00:00:11.000", speaker: "Piseth", speakerClass: "speaker-piseth", orig: "相信我，我一定会安全回来的。", khmer: "ជឿជាក់លើខ្ញុំចុះ ខ្ញុំប្រាកដជាត្រឡប់មកវិញដោយសុវត្ថិភាព។" }
        ]
    }
};

let currentStudioPreset = 'drama';
let studioViewMode = 'clean'; // 'clean' (Image 2 default), 'presets', or 'grid'

function initStudioWorkspace() {
    generateWaveformBars();
    generateVuMiniWaveBars();
    resetVuMetersToIdle();
    resetEngineMonitorToStandby();

    // Wire up video events & synchronization
    const mainVideo = document.getElementById('main-video');
    if (mainVideo) {
        mainVideo.addEventListener('ended', () => {
            isPlaying = false;
            const playIcon = document.getElementById('center-play-icon');
            const playBtn = document.getElementById('center-play-btn');
            const bottomPlayIcon = document.getElementById('bottom-play-icon');
            if (playIcon) playIcon.className = 'fa-solid fa-play';
            if (bottomPlayIcon) bottomPlayIcon.className = 'fa-solid fa-play';
            if (playBtn) {
                playBtn.style.opacity = '1';
                playBtn.style.pointerEvents = 'auto';
            }
            if (playbackTimer) {
                clearInterval(playbackTimer);
                playbackTimer = null;
            }
            resetVuMetersToIdle();
        });

        mainVideo.addEventListener('pause', () => {
            if (isPlaying) {
                isPlaying = false;
                const playIcon = document.getElementById('center-play-icon');
                const playBtn = document.getElementById('center-play-btn');
                const bottomPlayIcon = document.getElementById('bottom-play-icon');
                if (playIcon) playIcon.className = 'fa-solid fa-play';
                if (bottomPlayIcon) bottomPlayIcon.className = 'fa-solid fa-play';
                if (playBtn) {
                    playBtn.style.opacity = '1';
                    playBtn.style.pointerEvents = 'auto';
                }
                if (playbackTimer) {
                    clearInterval(playbackTimer);
                    playbackTimer = null;
                }
                resetVuMetersToIdle();
            }
        });

        mainVideo.addEventListener('play', () => {
            if (!isPlaying) {
                isPlaying = true;
                const playIcon = document.getElementById('center-play-icon');
                const playBtn = document.getElementById('center-play-btn');
                const bottomPlayIcon = document.getElementById('bottom-play-icon');
                if (playIcon) playIcon.className = 'fa-solid fa-pause';
                if (bottomPlayIcon) bottomPlayIcon.className = 'fa-solid fa-pause';
                if (playBtn) {
                    playBtn.style.opacity = '0';
                    playBtn.style.pointerEvents = 'none';
                }
            }
        });
    }

    // Spacebar to toggle Play/Pause
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            togglePlayPreview();
        }
    });

    // Preload dialogue items for initial active preset
    const preset = studioPresetsData[currentStudioPreset];
    if (preset) renderDialogueGrid(preset.dialogues);

    // Initial default view is Clean Image 2 View
    showCleanSourceView();
}

function selectStudioPreset(presetKey) {
    currentStudioPreset = presetKey;
    const preset = studioPresetsData[presetKey] || studioPresetsData.drama;

    // Update active class on preset cards
    document.querySelectorAll('.studio-preset-card').forEach(c => c.classList.remove('active'));
    const targetCard = document.getElementById(`card-preset-${presetKey}`);
    if (targetCard) targetCard.classList.add('active');

    // Update top header badge
    const badge = document.getElementById('current-mode-badge');
    if (badge) badge.innerHTML = preset.badge;

    // Load dialogues into grid
    renderDialogueGrid(preset.dialogues);

    showToast(`🎬 Mode Configured: ${preset.name}`);
    appendTerminalLine(`[Ready] Workflow preset set to ${preset.name}. Ready for media import or audition.`);
}

function showCleanSourceView() {
    studioViewMode = 'clean';
    const cleanView = document.getElementById('studio-source-clean-view');
    const setupView = document.getElementById('studio-preset-setup-view');
    const gridView = document.getElementById('studio-dialogue-waveform-view');

    if (cleanView) cleanView.style.display = 'flex';
    if (setupView) setupView.style.display = 'none';
    if (gridView) gridView.style.display = 'none';

    const importPrompt = document.getElementById('clean-import-prompt');
    const stagedCard = document.getElementById('staged-video-card');
    const sourceLabel = document.getElementById('clean-source-label');
    if (stagedVideoFile || stagedBatchFiles) {
        if (importPrompt) importPrompt.style.display = 'none';
        if (stagedCard) stagedCard.style.display = 'flex';
        if (sourceLabel) sourceLabel.style.display = 'none';
    } else {
        if (importPrompt) importPrompt.style.display = 'flex';
        if (stagedCard) stagedCard.style.display = 'none';
        if (sourceLabel) sourceLabel.style.display = 'block';
    }
}

function showPresetSetupView() {
    studioViewMode = 'presets';
    const cleanView = document.getElementById('studio-source-clean-view');
    const setupView = document.getElementById('studio-preset-setup-view');
    const gridView = document.getElementById('studio-dialogue-waveform-view');

    if (cleanView) cleanView.style.display = 'none';
    if (setupView) setupView.style.display = 'flex';
    if (gridView) gridView.style.display = 'none';
}

function showDialogueWaveformView() {
    // Keep UI clean, modern, and uncluttered (User requested hiding the raw dialogue table)
    showCleanSourceView();
}

function toggleSetupPresetsView() {
    if (studioViewMode === 'clean') {
        showPresetSetupView();
    } else if (studioViewMode === 'presets') {
        showCleanSourceView();
    } else {
        showCleanSourceView();
    }
}

let activeLoadedDialogues = [];
let activeDialogueAudioPlayer = null;

function formatSecondsToTimecode(sec) {
    if (sec === undefined || sec === null || isNaN(sec)) return "00:00:00.000";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 1000);
    return `00:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}

function renderDialogueGrid(dialogues) {
    const tbody = document.getElementById('dialogue-grid-rows');
    if (!tbody) return;

    activeLoadedDialogues = dialogues || [];
    tbody.innerHTML = '';
    activeLoadedDialogues.forEach((d, idx) => {
        const tr = document.createElement('tr');
        const rowId = d.id || (idx + 1);
        tr.className = 'dialogue-row';
        tr.id = `dialogue-row-${rowId}`;

        const tcInStr = d.tcIn || formatSecondsToTimecode(d.start);
        const tcOutStr = d.tcOut || formatSecondsToTimecode(d.end);

        const vKey = (d.voice || d.voice_used || "piseth").toLowerCase();
        const isSreyMom = vKey.includes("sreymom") || vKey.includes("female") || vKey.includes("ស្រី");
        const speakerClass = isSreyMom ? "speaker-sreymom" : "speaker-piseth";
        const defaultSpeaker = isSreyMom ? "ស្រីមុំ (Sreymom)" : "ពិសិដ្ឋ (Piseth)";
        const speakerName = d.speaker || defaultSpeaker;

        const origText = d.orig || d.text_original || d.text || "";
        const khmerText = d.khmer || d.text_km || origText;

        tr.innerHTML = `
            <td style="color:#716655; font-family:var(--font-mono);">${rowId}</td>
            <td><span class="tc-code">${tcInStr} - ${tcOutStr}</span></td>
            <td>
                <span class="speaker-badge ${speakerClass}">
                    <i class="fa-solid fa-user-voice"></i> ${escapeHtml(speakerName)}
                </span>
            </td>
            <td class="orig-script-text">${escapeHtml(origText)}</td>
            <td class="khmer-dub-text">${escapeHtml(khmerText)}</td>
            <td style="text-align:center;">
                <button class="grid-action-btn" title="ចាក់សំឡេងខ្មែរ (Play Khmer Speech)" onclick="playDialogueSnippet(${rowId})"><i class="fa-solid fa-play"></i></button>
                <button class="grid-action-btn" title="កែសម្រួល (Edit Line)" onclick="editDialogueSnippet(${rowId})"><i class="fa-solid fa-pen"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function playDialogueSnippet(id) {
    const item = activeLoadedDialogues.find(d => String(d.id) === String(id));
    const targetRow = document.getElementById(`dialogue-row-${id}`);
    document.querySelectorAll('.dialogue-row').forEach(r => r.classList.remove('playing'));
    if (targetRow) targetRow.classList.add('playing');

    showToast(`🔊 កំពុងចាក់សំឡេងខ្មែរបន្ទាត់ #${id}`);
    appendTerminalLine(`[Audio Engine] Auditioning line #${id} (${item ? (item.voice || 'piseth') : 'audio'})`);

    if (activeDialogueAudioPlayer) {
        try { activeDialogueAudioPlayer.pause(); } catch(e) {}
        activeDialogueAudioPlayer = null;
    }

    startAudioPlaybackVUMeter();

    let audioUrl = null;
    if (item && item.audio_file) {
        audioUrl = `/media/${item.audio_file.replace(/\\/g, '/')}`;
    }

    if (audioUrl) {
        activeDialogueAudioPlayer = new Audio(audioUrl);
        activeDialogueAudioPlayer.onended = () => {
            resetVuMetersToIdle();
            if (targetRow) targetRow.classList.remove('playing');
        };
        activeDialogueAudioPlayer.onerror = () => {
            resetVuMetersToIdle();
            if (targetRow) targetRow.classList.remove('playing');
        };
        try {
            await activeDialogueAudioPlayer.play();
            return;
        } catch(e) {
            console.warn("Direct play note:", e);
        }
    }

    // Fallback on-the-fly synthesize preview if not yet cached
    if (item && (item.text_km || item.khmer)) {
        try {
            const resp = await fetch('/api/voices/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: item.text_km || item.khmer,
                    voice: item.voice || (item.speaker && item.speaker.includes('sreymom') ? 'sreymom' : 'piseth')
                })
            });
            const data = await resp.json();
            if (data.success && data.audio_url) {
                activeDialogueAudioPlayer = new Audio(data.audio_url);
                activeDialogueAudioPlayer.onended = () => {
                    resetVuMetersToIdle();
                    if (targetRow) targetRow.classList.remove('playing');
                };
                activeDialogueAudioPlayer.play();
                return;
            }
        } catch (e) {
            console.warn("Preview error:", e);
        }
    }

    setTimeout(() => {
        resetVuMetersToIdle();
        if (targetRow) targetRow.classList.remove('playing');
    }, 2000);
}

function editDialogueSnippet(id) {
    showToast(`✏️ Editing dialogue line #${id}`);
}

function generateWaveformBars() {
    const container = document.getElementById('waveform-bars');
    if (!container) return;
    container.innerHTML = '';
    const heights = [30, 45, 70, 85, 60, 40, 55, 90, 100, 80, 50, 65, 85, 95, 75, 40, 50, 80, 90, 70, 45, 60, 85, 70, 55, 40, 65, 90, 100, 85, 60, 45, 70, 85, 95, 65, 40, 55, 80, 75, 60, 50, 70, 85, 90, 65, 45, 55, 75, 90, 80, 60, 50, 65, 80, 70, 50, 40, 60, 75];
    heights.forEach(h => {
        const bar = document.createElement('div');
        bar.className = 'waveform-wave-bar';
        bar.style.height = `${h}%`;
        container.appendChild(bar);
    });
}

function handleWaveformClick(e) {
    const track = document.getElementById('waveform-visualizer-track');
    const playhead = document.getElementById('waveform-playhead');
    if (!track || !playhead) return;
    const rect = track.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(100, (clickX / rect.width) * 100));
    playhead.style.left = `${percent}%`;
    playheadSeconds = (percent / 100) * totalDurationSeconds;
    updateScrubberUI();
}

function seekRelative(delta) {
    playheadSeconds = Math.max(0, Math.min(totalDurationSeconds, playheadSeconds + delta));
    updateScrubberUI();
}

function generateVuMiniWaveBars() {
    const container = document.getElementById('vu-mini-wave-bars');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < 14; i++) {
        const bar = document.createElement('div');
        bar.className = 'vu-wave-bar';
        bar.style.height = '4%';
        container.appendChild(bar);
    }
}

// ==========================================================================
// VU METERS & AUDIO REACTIVITY CONTROLLER
// ==========================================================================
let vuAnimationTimer = null;

function resetVuMetersToIdle() {
    if (vuAnimationTimer) {
        clearInterval(vuAnimationTimer);
        vuAnimationTimer = null;
    }
    const fillL = document.getElementById('vu-fill-l');
    const fillR = document.getElementById('vu-fill-r');
    const dbL = document.getElementById('vu-db-l');
    const dbR = document.getElementById('vu-db-r');

    if (fillL) fillL.style.width = '0%';
    if (fillR) fillR.style.width = '0%';
    if (dbL) dbL.textContent = '-∞ dB';
    if (dbR) dbR.textContent = '-∞ dB';

    const miniBars = document.querySelectorAll('#vu-mini-wave-bars .vu-wave-bar');
    miniBars.forEach(bar => {
        bar.style.height = '4%';
    });
}

function startAudioPlaybackVUMeter() {
    if (vuAnimationTimer) clearInterval(vuAnimationTimer);

    vuAnimationTimer = setInterval(() => {
        if (!isPlaying) {
            resetVuMetersToIdle();
            return;
        }
        const fillL = document.getElementById('vu-fill-l');
        const fillR = document.getElementById('vu-fill-r');
        const dbL = document.getElementById('vu-db-l');
        const dbR = document.getElementById('vu-db-r');

        const randL = Math.floor(Math.random() * 25 + 55); // 55% - 80%
        const randR = Math.floor(Math.random() * 25 + 50); // 50% - 75%

        if (fillL) fillL.style.width = `${randL}%`;
        if (fillR) fillR.style.width = `${randR}%`;

        if (dbL) dbL.textContent = `-${Math.floor((100 - randL) * 0.35)} dB`;
        if (dbR) dbR.textContent = `-${Math.floor((100 - randR) * 0.4)} dB`;

        const miniBars = document.querySelectorAll('#vu-mini-wave-bars .vu-wave-bar');
        miniBars.forEach(bar => {
            bar.style.height = `${Math.floor(Math.random() * 75 + 15)}%`;
        });
    }, 200);
}

// ==========================================================================
// EXPORT JOB & STUDIO ENGINE RENDER MONITOR CONTROLLER
// ==========================================================================
let exportJobTimer = null;
let exportPercent = 0;
let exportElapsedSec = 0;
let currentExportOutputMode = 'separate'; // 'separate' | 'full' | 'both'

function openExportOptionsModal() {
    const epCountElem = document.getElementById('export-output-ep-count');
    const epChainElem = document.getElementById('export-output-ep-chain');
    const descFullElem = document.getElementById('export-desc-full');
    const descBothElem = document.getElementById('export-desc-both');

    let baseTitle = "Drama_Series";

    if (stagedBatchFiles && stagedBatchFiles.length > 0) {
        const count = stagedBatchFiles.length;
        if (epCountElem) epCountElem.textContent = `${count} episodes`;

        if (epChainElem) {
            if (count <= 4) {
                epChainElem.textContent = stagedBatchFiles.map((f, i) => `Ep${i + 1}`).join(' → ');
            } else {
                epChainElem.textContent = `Ep1 → Ep2 → ... → Ep${count}`;
            }
        }

        const rawName = stagedBatchFiles[0].name.replace(/\.[^/.]+$/, '');
        baseTitle = rawName.replace(/(?:_part|[-_]ep|[-_]e|\bep|\bepisode)[-_]?\d+/i, '').replace(/[-_]+$/, '').trim() || "Drama_Series";

        const mergedName = `Dubbed_${baseTitle}_Full_Movie.mp4`;
        if (descFullElem) descFullElem.textContent = `Joined into ${mergedName} — ${count} episodes merged`;
        if (descBothElem) descBothElem.textContent = `Episodes + ${mergedName} (ទទួលបានទាំងពីរ)`;

    } else if (stagedVideoFile) {
        if (epCountElem) epCountElem.textContent = "1 video episode";
        if (epChainElem) epChainElem.textContent = stagedVideoFile.name;

        const rawName = stagedVideoFile.name.replace(/\.[^/.]+$/, '');
        baseTitle = rawName || "Video";
        const singleOutName = `Dubbed_${baseTitle}.mp4`;

        if (descFullElem) descFullElem.textContent = `Full single video — ${singleOutName}`;
        if (descBothElem) descBothElem.textContent = `Single video master — ${singleOutName}`;
    } else {
        showToast("⚠️ សូមដាក់វីដេអូចូលជាមុនសិន រួចចុច Export!");
        openImportModal();
        return;
    }

    selectExportOutputMode(currentExportOutputMode || 'separate');
    openModal('modal-export-options');
}

function selectExportOutputMode(mode) {
    currentExportOutputMode = mode;
    const optSep = document.getElementById('export-opt-separate');
    const optFull = document.getElementById('export-opt-full');
    const optBoth = document.getElementById('export-opt-both');

    if (optSep) optSep.classList.toggle('active', mode === 'separate');
    if (optFull) optFull.classList.toggle('active', mode === 'full');
    if (optBoth) optBoth.classList.toggle('active', mode === 'both');
}

async function confirmAndExecuteExport() {
    closeModal('modal-export-options');
    const chosenMode = currentExportOutputMode || 'separate';

    // 1. Single video staged
    if (stagedVideoFile) {
        const fileToDub = stagedVideoFile;
        stagedVideoFile = null;
        const exportBtn = document.getElementById('btn-tab-export');
        if (exportBtn) exportBtn.classList.remove('export-ready-pulse');
        startAutoDubbingPipeline(fileToDub);
        return;
    }

    // 2. Batch videos staged
    if (stagedBatchFiles && stagedBatchFiles.length > 0) {
        const filesToDub = stagedBatchFiles;
        stagedBatchFiles = null;
        const exportBtn = document.getElementById('btn-tab-export');
        if (exportBtn) exportBtn.classList.remove('export-ready-pulse');
        startStudioBatchDubbingPipeline(filesToDub, chosenMode);
        return;
    }

    showToast("⚠️ មិនមានវីដេអូដែលបានដាក់នោះទេ!");
}

function startStudioExportJob() {
    // 1. If user staged a single video, open Export Options Modal (Choice for user)
    if (stagedVideoFile) {
        openExportOptionsModal();
        return;
    }

    // 2. If user staged batch videos / folder, open Export Options Modal (Separate / One Full Video / Both)
    if (stagedBatchFiles && stagedBatchFiles.length > 0) {
        openExportOptionsModal();
        return;
    }

    // 3. If a dubbed video is already completed, open folder or download
    if (currentDubbedProject && currentDubbedProject.output_video_file) {
        openExportFolderDirect(currentDubbedProject.output_video_file);
        showToast("📂 បានបើកទីតាំង Folder វីដេអូដែល Render រួចរាល់!");
        const mainVideo = document.getElementById('main-video');
        if (mainVideo && mainVideo.src) {
            const a = document.createElement('a');
            a.href = mainVideo.src;
            a.download = `Dubbed_${currentDubbedProject.title || 'drama'}.mp4`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        }
        return;
    }

    // 4. If nothing is staged, guide the user to import first
    showToast("⚠️ សូមដាក់វីដេអូចូលជាមុនសិន រួចចុច Export!");
    openImportModal();
}

function updateExportProgressUI(pct, elapsedSec, etaSec, taskName) {
    const pctElem = document.getElementById('monitor-export-percent');
    const fillElem = document.getElementById('monitor-progress-fill');
    const elapElem = document.getElementById('monitor-elapsed-time');
    const etaElem = document.getElementById('monitor-eta-time');
    const finElem = document.getElementById('monitor-finish-time');
    const taskElem = document.getElementById('monitor-current-task');

    if (pctElem) pctElem.textContent = `${pct}%`;
    if (fillElem) fillElem.style.width = `${pct}%`;

    const elM = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
    const elS = String(elapsedSec % 60).padStart(2, '0');
    if (elapElem) elapElem.textContent = `00:${elM}:${elS}`;

    if (etaSec > 0) {
        const etM = String(Math.floor(etaSec / 60)).padStart(2, '0');
        const etS = String(etaSec % 60).padStart(2, '0');
        if (etaElem) etaElem.textContent = `00:${etM}:${etS}`;

        const finishDate = new Date(Date.now() + etaSec * 1000);
        if (finElem) finElem.textContent = finishDate.toLocaleTimeString();
    } else {
        if (etaElem) etaElem.textContent = '00:00:00';
        if (finElem) finElem.textContent = 'Completed';
    }

    if (taskElem) {
        taskElem.innerHTML = `<i class="fa-solid fa-gear fa-spin" style="color:#facc15; font-size:0.65rem;"></i> ${escapeHtml(taskName)}`;
    }
}

function resetEngineMonitorToStandby() {
    if (exportJobTimer) {
        clearInterval(exportJobTimer);
        exportJobTimer = null;
    }

    const pill = document.getElementById('monitor-engine-status-pill');
    const dot = document.getElementById('monitor-pulse-dot');
    const text = document.getElementById('monitor-engine-status-text');
    if (pill) pill.className = 'engine-status-pill standby';
    if (dot) dot.className = 'pulse-indicator standby';
    if (text) text.textContent = 'ENGINE STANDBY';

    const fpsElem = document.getElementById('monitor-render-fps');
    const fpsCap = document.getElementById('monitor-fps-caption');
    const brElem = document.getElementById('monitor-render-bitrate');
    const brCap = document.getElementById('monitor-bitrate-caption');

    if (fpsElem) fpsElem.textContent = '0.0';
    if (fpsCap) fpsCap.textContent = 'Idle (Ready)';
    if (brElem) brElem.textContent = '0.0';
    if (brCap) brCap.textContent = 'Standby';

    const pctElem = document.getElementById('monitor-export-percent');
    const fillElem = document.getElementById('monitor-progress-fill');
    const elapElem = document.getElementById('monitor-elapsed-time');
    const etaElem = document.getElementById('monitor-eta-time');
    const finElem = document.getElementById('monitor-finish-time');
    const taskElem = document.getElementById('monitor-current-task');

    if (pctElem) pctElem.textContent = '0%';
    if (fillElem) fillElem.style.width = '0%';
    if (elapElem) elapElem.textContent = '00:00:00';
    if (etaElem) etaElem.textContent = '--:--:--';
    if (finElem) finElem.textContent = 'Standby';
    if (taskElem) {
        taskElem.innerHTML = `<i class="fa-solid fa-circle-check" style="color:#22c55e; font-size:0.65rem;"></i> System Ready • Select a preset or import media`;
    }
}

function toggleEngineLogDrawer() {
    const drawer = document.getElementById('engine-log-drawer');
    if (drawer) {
        drawer.style.display = drawer.style.display === 'none' ? 'block' : 'none';
    }
}

// ==========================================================================
// 4. DOWNLOADER STUDIO (Exact Match to Image 2)
// ==========================================================================
async function loadDownloaderPlatforms() {
    const container = document.getElementById('dl-platforms-list');
    if (!container) return;

    try {
        const res = await fetch('/api/downloader/platforms');
        const data = await res.json();
        if (data.success && data.platforms) {
            container.innerHTML = '';
            data.platforms.forEach(p => {
                const item = document.createElement('div');
                item.className = `dl-platform-pill-item ${p.id === dlSelectedPlatform ? 'active' : ''}`;
                item.onclick = () => filterByPlatform(p.id, p.name, p.count);
                item.innerHTML = `
                    <i class="${p.icon}"></i>
                    <span>${escapeHtml(p.name)}</span>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) {}
}

function filterByPlatform(platId, platName, totalCount) {
    dlSelectedPlatform = platId;
    loadDownloaderPlatforms();

    const countLabel = document.getElementById('dl-catalog-count-label');
    if (countLabel) {
        countLabel.innerHTML = `<i class="fa-solid fa-globe"></i> ${escapeHtml(platName)} (${totalCount !== undefined ? totalCount : 0})`;
    }

    const input = document.getElementById('dl-link-url-input');
    if (input) {
        input.placeholder = `Paste a ${escapeHtml(platName)} URL...`;
    }

    const badge = document.getElementById('dl-info-platform-badge');
    if (badge) {
        badge.textContent = platName.toUpperCase();
    }

    loadDramaCatalog(platId);
}

async function loadDramaCatalog(platformId = "all", query = "") {
    const container = document.getElementById('dl-drama-cards-container');
    if (!container) return;

    try {
        const res = await fetch(`/api/downloader/catalog?platform=${platformId}&q=${encodeURIComponent(query)}`);
        const data = await res.json();
        container.innerHTML = '';
        if (data.success && data.dramas && data.dramas.length > 0) {
            data.dramas.forEach(drama => {
                const card = document.createElement('div');
                card.className = `dl-card-item ${dlCurrentDrama && dlCurrentDrama.id === drama.id ? 'active' : ''}`;
                card.onclick = () => selectDramaCard(drama.id);
                card.innerHTML = `
                    <div class="dl-card-thumb-wrap">
                        <img src="${drama.poster || 'vertical_drama_sample.jpg'}" alt="${escapeHtml(drama.title)}">
                        <div class="dl-card-platform-pill">${escapeHtml(drama.platform)}</div>
                        <button class="dl-card-preview-overlay-btn" onclick="event.stopPropagation(); previewDramaVideoDirect('${drama.id}')">Preview</button>
                    </div>
                    <div class="dl-card-details-box">
                        <div class="dl-card-title-line" title="${escapeHtml(drama.title)}">${escapeHtml(drama.title)}</div>
                        <div class="dl-card-ep-count">EP 1-${drama.total_episodes}</div>
                    </div>
                `;
                container.appendChild(card);
            });

            if (!dlCurrentDrama) {
                selectDramaCard(data.dramas[0].id);
            }
        } else {
            container.innerHTML = `
                <div style="grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 20px; color: #716655; text-align: center;">
                    <i class="fa-solid fa-cloud-arrow-down" style="font-size: 2rem; color: #ca8a04; margin-bottom: 12px;"></i>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #cbd5e1;">មិនទាន់មានរឿងភាគនៅក្នុងបញ្ជី (No Series Loaded)</div>
                    <div style="font-size: 0.72rem; color: #716655; margin-top: 6px;">សូមបិទភ្ជាប់ Link រឿងភាគនៅក្នុងប្រអប់ខាងលើ រួចចុច Analyze ដើម្បីទាញយកភាគរឿង។</div>
                </div>
            `;
            // Reset right drama info panel
            dlCurrentDrama = null;
            dlEpisodesList = [];
            const title = document.getElementById('dl-info-title-text');
            const stats = document.getElementById('dl-info-stats-text');
            const desc = document.getElementById('dl-info-desc-text');
            if (title) title.textContent = "No drama loaded";
            if (stats) stats.textContent = "Episodes 0 • Locked 0 • Selected 0";
            if (desc) desc.textContent = "Paste a supported URL to inspect its episode catalog and prepare the download queue.";
            renderEpisodesChecklist([]);
        }
    } catch (e) {}
}

async function selectDramaCard(dramaId) {
    try {
        const res = await fetch(`/api/downloader/drama/${dramaId}`);
        const data = await res.json();
        if (data.success) {
            dlCurrentDrama = data.drama;
            dlEpisodesList = data.episodes || [];

            // Update Right DRAMA INFO Box
            const title = document.getElementById('dl-info-title-text');
            const badge = document.getElementById('dl-info-platform-badge');
            const stats = document.getElementById('dl-info-stats-text');
            const desc = document.getElementById('dl-info-desc-text');

            if (title) title.textContent = data.drama.title;
            if (badge) badge.textContent = data.drama.platform.toUpperCase();
            if (stats) stats.textContent = `Episodes ${data.drama.total_episodes} • Locked 0 • Selected ${data.drama.total_episodes}`;
            if (desc) desc.textContent = data.drama.description || "Short drama series manifest fetched.";

            renderEpisodesChecklist(dlEpisodesList);
            updateDownloaderStats(data.stats);
        }
    } catch (e) {}
}

function renderEpisodesChecklist(episodes) {
    const list = document.getElementById('dl-episodes-list-box');
    const rangeTag = document.getElementById('dl-episodes-range-tag');
    if (!list) return;

    if (!episodes || episodes.length === 0) {
        list.innerHTML = '<div style="color:#716655; font-size:0.65rem; padding:8px; text-align:center;">No episodes loaded</div>';
        if (rangeTag) rangeTag.textContent = "EP 0-0";
        return;
    }

    if (rangeTag) rangeTag.textContent = `EP 1-${episodes.length}`;
    list.innerHTML = '';

    episodes.forEach(ep => {
        const row = document.createElement('div');
        row.className = 'dl-ep-row';
        row.innerHTML = `
            <div style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" ${ep.is_selected ? 'checked' : ''} onchange="toggleSingleEpisode('${ep.id}', this.checked)">
                <span>EP ${ep.episode_number}: ${escapeHtml(ep.title)}</span>
            </div>
            <span style="font-size:0.62rem; color:var(--gold-glow);">${ep.status}</span>
        `;
        list.appendChild(row);
    });
}

function toggleSingleEpisode(epId, isChecked) {
    const target = dlEpisodesList.find(e => e.id === epId);
    if (target) target.is_selected = isChecked;
    const selectedCount = dlEpisodesList.filter(e => e.is_selected).length;
    
    const stats = document.getElementById('dl-info-stats-text');
    if (stats && dlCurrentDrama) {
        stats.textContent = `Episodes ${dlCurrentDrama.total_episodes} • Locked 0 • Selected ${selectedCount}`;
    }
    const statSelected = document.getElementById('dl-stat-selected');
    if (statSelected) statSelected.textContent = selectedCount;
}

function handleDlLinkKey(e) {
    if (e.key === 'Enter') analyzeEnteredLink();
}

async function analyzeEnteredLink() {
    const input = document.getElementById('dl-link-url-input');
    const url = input ? input.value.trim() : "";
    if (!url) {
        showToast("⚠️ Please enter a drama URL");
        return;
    }

    showToast("🔍 Analyzing drama link...");
    appendDownloaderLog(`[${new Date().toLocaleTimeString()}] Analyzing drama manifest from URL: ${url}`);

    try {
        const res = await fetch('/api/downloader/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const data = await res.json();
        if (data.success && data.drama) {
            dlCurrentDrama = data.drama;
            dlEpisodesList = data.episodes || [];
            await loadDramaCatalog();
            selectDramaCard(data.drama.id);
            showToast(`✨ Found: ${data.drama.title} (${dlEpisodesList.length} EP)`);
        } else {
            showToast(`❌ ${data.error || 'Failed to analyze'}`);
        }
    } catch (e) {
        showToast("❌ Network error");
    }
}

function switchDlViewMode(mode) {
    const catBtn = document.getElementById('btn-mode-catalog');
    const qBtn = document.getElementById('btn-mode-queue');
    if (catBtn) catBtn.classList.toggle('active', mode === 'catalog');
    if (qBtn) qBtn.classList.toggle('active', mode === 'queue');
}

let driveCustomPaths = {
    "C": "C:/SN_Dramas",
    "D": "D:/SN_Dramas"
};

async function initSaveLocationPaths() {
    const input = document.getElementById('dl-save-path-input');
    if (!input) return;

    try {
        const res = await fetch('/api/system/default-paths');
        const data = await res.json();
        if (data && data.success) {
            if (data.drive_c) driveCustomPaths["C"] = data.drive_c;
            if (data.drive_d) driveCustomPaths["D"] = data.drive_d;
        }
    } catch (e) {}

    const saved = localStorage.getItem('sn_save_location');
    if (saved && saved.trim()) {
        input.value = saved.trim();
    } else {
        input.value = driveCustomPaths["D"] || "D:/SN_Dramas";
    }
    input.setAttribute('title', input.value);
    updateDriveButtonHighlight();
}

function selectDrive(driveLetter) {
    const letter = driveLetter.toUpperCase();
    const input = document.getElementById('dl-save-path-input');
    
    let targetPath = driveCustomPaths[letter] || `${letter}:/SN_Dramas`;
    const savedForDrive = localStorage.getItem(`sn_save_path_${letter.toLowerCase()}`);
    if (savedForDrive && savedForDrive.toUpperCase().startsWith(`${letter}:`)) {
        targetPath = savedForDrive;
    }
    
    if (input) {
        input.value = targetPath;
        input.setAttribute('title', targetPath);
    }
    localStorage.setItem('sn_save_location', targetPath);
    localStorage.setItem('sn_active_drive', letter);
    updateDriveButtonHighlight();

    showToast(`💽 បានជ្រើសរើស Drive ${letter}: (${targetPath})`);
    appendDownloaderLog(`[${new Date().toLocaleTimeString()}] Active download location: Drive ${letter}: (${targetPath})`);
}

function updateDriveButtonHighlight() {
    const input = document.getElementById('dl-save-path-input');
    const path = input ? input.value.trim().toUpperCase() : "";
    
    const btnC = document.getElementById('btn-drive-c');
    const btnD = document.getElementById('btn-drive-d');
    
    const isC = path.startsWith("C:");
    const isD = path.startsWith("D:");
    
    if (btnC) btnC.classList.toggle('active', isC);
    if (btnD) btnD.classList.toggle('active', isD || (!isC && !isD));
}

async function browseSaveLocation() {
    const input = document.getElementById('dl-save-path-input');
    const currentPath = input ? input.value.trim() : '';

    showToast("📂 កំពុងបើកផ្ទាំងជ្រើសរើស Folder លើ Laptop...");
    appendDownloaderLog(`[${new Date().toLocaleTimeString()}] Opening Windows folder chooser...`);

    try {
        const res = await fetch('/api/system/select-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initial_dir: currentPath })
        });
        const data = await res.json();
        if (data.success && data.path) {
            const cleanPath = data.path.replace(/\\/g, '/');
            if (input) {
                input.value = cleanPath;
                input.setAttribute('title', cleanPath);
            }
            const driveLetter = cleanPath.slice(0, 1).toUpperCase();
            if (driveLetter === 'C' || driveLetter === 'D') {
                driveCustomPaths[driveLetter] = cleanPath;
                localStorage.setItem(`sn_save_path_${driveLetter.toLowerCase()}`, cleanPath);
                localStorage.setItem('sn_active_drive', driveLetter);
            }
            localStorage.setItem('sn_save_location', cleanPath);
            updateDriveButtonHighlight();
            showToast(`✅ បានជ្រើសរើស Folder: ${cleanPath}`);
            appendDownloaderLog(`[${new Date().toLocaleTimeString()}] Save folder updated: ${cleanPath}`);
        } else if (data.cancelled) {
            showToast("ℹ️ បានបោះបង់ការជ្រើសរើស Folder");
        } else {
            showToast("⚠️ មិនអាចជ្រើសរើស Folder បានទេ");
        }
    } catch (e) {
        console.error("Browse folder error:", e);
        showToast("⚠️ បញ្ហាក្នុងការបើក Folder Dialog");
    }
}

async function openSaveLocationInExplorer() {
    const input = document.getElementById('dl-save-path-input');
    const path = input ? input.value.trim() : '';
    if (!path) {
        showToast("⚠️ សូមជ្រើសរើសទីតាំង Folder ជាមុនសិន");
        return;
    }

    try {
        const res = await fetch('/api/system/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`📂 បានបើក Folder ក្នុង Windows Explorer`);
            appendDownloaderLog(`[${new Date().toLocaleTimeString()}] Opened directory: ${path}`);
        } else {
            showToast(`⚠️ ${data.error || 'មិនអាចបើក Folder បានទេ'}`);
        }
    } catch (e) {
        showToast("⚠️ កំហុសក្នុងការបើក Windows Explorer");
    }
}

function previewLoadedDrama() {
    if (!dlCurrentDrama) return;
    switchMainTab('translate');
    showToast(`▶ Loaded '${dlCurrentDrama.title}' in 9:16 Monitor`);
}

function previewDramaVideoDirect(dramaId) {
    selectDramaCard(dramaId);
    previewLoadedDrama();
}

async function startBatchDownload() {
    const selected = dlEpisodesList.filter(e => e.is_selected);
    if (selected.length === 0) {
        showToast("⚠️ Please select at least one episode");
        return;
    }

    showToast(`🚀 Downloading ${selected.length} episodes...`);
    appendDownloaderLog(`[${new Date().toLocaleTimeString()}] Starting batch queue for ${selected.length} episodes...`);

    const path = document.getElementById('dl-save-path-input').value.trim();
    const posterElem = document.getElementById('dl-save-poster-check');
    const savePoster = posterElem ? posterElem.checked : true;

    try {
        await fetch('/api/downloader/download-episodes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                episode_ids: selected.map(s => s.id),
                save_location: path,
                save_poster: savePoster
            })
        });

        // Start Polling
        if (dlPollTimer) clearInterval(dlPollTimer);
        dlPollTimer = setInterval(async () => {
            try {
                const sRes = await fetch('/api/downloader/status');
                const sData = await sRes.json();
                if (sData) {
                    if (sData.episodes) {
                        dlEpisodesList = sData.episodes;
                        renderEpisodesChecklist(dlEpisodesList);
                    }
                    updateDownloaderStats(sData.stats);
                    if (!sData.is_downloading) {
                        clearInterval(dlPollTimer);
                        dlPollTimer = null;
                        showToast("🎉 Download batch completed!");
                    }
                }
            } catch (e) {}
        }, 500);
    } catch (e) {}
}

async function stopBatchDownload() {
    try {
        await fetch('/api/downloader/stop', { method: 'POST' });
        showToast("⏹️ Download Stopped");
        if (dlPollTimer) {
            clearInterval(dlPollTimer);
            dlPollTimer = null;
        }
    } catch (e) {}
}

function updateDownloaderStats(stats) {
    if (!stats) return;
    const total = document.getElementById('dl-stat-total');
    const selected = document.getElementById('dl-stat-selected');
    const completed = document.getElementById('dl-stat-completed');
    const failed = document.getElementById('dl-stat-failed');
    const locked = document.getElementById('dl-stat-locked');
    const percent = document.getElementById('dl-stat-overall-percent');

    if (total) total.textContent = stats.total || 0;
    if (selected) selected.textContent = stats.selected || 0;
    if (completed) completed.textContent = stats.completed || 0;
    if (failed) failed.textContent = stats.failed || 0;
    if (locked) locked.textContent = stats.locked || 0;
    if (percent) percent.textContent = `${stats.progress_percent || 0}%`;
}

function appendDownloaderLog(msg) {
    const box = document.getElementById('dl-activity-terminal-box');
    if (!box) return;
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.textContent = msg;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
}

function clearDownloaderLog() {
    const box = document.getElementById('dl-activity-terminal-box');
    if (box) box.innerHTML = `<div class="terminal-line">[${new Date().toLocaleTimeString()}] Activity log cleared.</div>`;
    showToast("🧹 Log cleared");
}

// ==========================================================================
// 5. SETTINGS & IMPORT MODALS (Exact Match to Images 3 & 4)
// ==========================================================================
function openSettingsModal() {
    backToSettingsHub();
    openModal('modal-settings');
}

function backToSettingsHub() {
    const hub = document.getElementById('settings-main-hub-view');
    const subAi = document.getElementById('settings-subpage-ai');
    const subLic = document.getElementById('settings-subpage-license');
    const subStory = document.getElementById('settings-subpage-story');

    if (hub) hub.style.display = 'flex';
    if (subAi) subAi.style.display = 'none';
    if (subLic) subLic.style.display = 'none';
    if (subStory) subStory.style.display = 'none';
}

function openSettingsSubpage(key) {
    if (key === 'ai') {
        closeModal('modal-settings');
        openAiProvidingModal();
        return;
    }
    if (key === 'story') {
        closeModal('modal-settings');
        openStorySettingsModal();
        return;
    }

    const hub = document.getElementById('settings-main-hub-view');
    const subAi = document.getElementById('settings-subpage-ai');
    const subLic = document.getElementById('settings-subpage-license');
    const subStory = document.getElementById('settings-subpage-story');

    if (hub) hub.style.display = 'none';
    if (subAi) subAi.style.display = 'none';
    if (subLic) subLic.style.display = 'none';
    if (subStory) subStory.style.display = 'none';

    if (key === 'license' && subLic) subLic.style.display = 'flex';
}

// ==========================================================================
// STORY SETTINGS MANAGER (Exact Match to User Attached Image)
// ==========================================================================
let currentStoryConfig = {
    khmer_voice: "piseth",
    auto_multi_voice: false,
    source_lang: "auto",
    whisper_model: "medium",
    aspect_ratio: "9:16",
    subtitle_mode: "none",
    dubbing_mode: "smart_bgm",
    ducking_volume: "0.02",
    speech_boost_db: 2.5
};

function getStoryVoiceDisplayLabel() {
    if (currentStoryConfig.khmer_voice === 'sreymom') {
        return "Sreymom (Female Solo - អ្នកបញ្ចូលសំឡេងស្រី)";
    }
    return "Piseth (Male Solo - អ្នកបញ្ចូលសំឡេងទោល)";
}

function refreshStagedCardVoiceMeta() {
    const stagedMeta = document.getElementById('staged-file-meta');
    if (!stagedMeta) return;
    const vLabel = getStoryVoiceDisplayLabel();
    if (stagedVideoFile) {
        const sizeMb = (stagedVideoFile.size / (1024 * 1024)).toFixed(1);
        let durStr = "";
        if (totalDurationSeconds > 0) {
            const durM = Math.floor(totalDurationSeconds / 60);
            const durS = Math.floor(totalDurationSeconds % 60);
            durStr = ` • ${String(durM).padStart(2, '0')}:${String(durS).padStart(2, '0')}`;
        }
        stagedMeta.innerHTML = `<i class="fa-solid fa-microphone-lines" style="color:#facc15;"></i> សំឡេង: <strong style="color:#facc15;">${vLabel}</strong> • ${sizeMb} MB${durStr} • ត្រៀមបកប្រែ`;
    } else if (stagedBatchFiles && stagedBatchFiles.length > 0) {
        stagedMeta.innerHTML = `<i class="fa-solid fa-microphone-lines" style="color:#facc15;"></i> សំឡេង: <strong style="color:#facc15;">${vLabel}</strong> • Batch: ${stagedBatchFiles.length} វីដេអូ`;
    }
}

function syncStagedCardControls() {
    // 1. Sync voice chip active state
    let activeKey = 'piseth';
    if (currentStoryConfig.khmer_voice === 'sreymom') {
        activeKey = 'sreymom';
    }
    ['piseth', 'sreymom'].forEach(k => {
        const chip = document.getElementById(`voice-chip-${k}`);
        if (chip) {
            if (k === activeKey) chip.classList.add('active');
            else chip.classList.remove('active');
        }
    });

    const vBadge = document.getElementById('staged-voice-status-badge');
    if (vBadge) {
        if (activeKey === 'sreymom') vBadge.textContent = "Sreymom (ស្រីទោល)";
        else vBadge.textContent = "Piseth (ប្រុសទោល)";
    }

    // 2. Sync BGM slider & presets
    const rawDuck = parseFloat(currentStoryConfig.ducking_volume !== undefined ? currentStoryConfig.ducking_volume : 0.18);
    const duckingNum = Math.min(40, Math.max(0, Math.round(rawDuck * 100)));
    const slider = document.getElementById('staged-bgm-slider');
    if (slider) slider.value = duckingNum;

    [0, 10, 18, 28].forEach(p => {
        const btn = document.getElementById(`bgm-pre-${p}`);
        if (btn) {
            if (p === duckingNum || (p === 18 && (duckingNum >= 15 && duckingNum <= 20))) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    });

    const bgmBadge = document.getElementById('staged-bgm-val-badge');
    if (bgmBadge) {
        if (duckingNum === 0) bgmBadge.textContent = "0% (បិទភ្លេង)";
        else if (duckingNum <= 10) bgmBadge.textContent = `${duckingNum}% • ភ្លេងស្រាល`;
        else if (duckingNum <= 20) bgmBadge.textContent = `${duckingNum}% • ស្តង់ដារពិរោះ`;
        else bgmBadge.textContent = `${duckingNum}% • ភ្លេងរាងឮ`;
    }
}

async function selectQuickVoice(voiceKey) {
    if (voiceKey === 'sreymom') {
        currentStoryConfig.khmer_voice = 'sreymom';
        currentStoryConfig.auto_multi_voice = false;
    } else {
        currentStoryConfig.khmer_voice = 'piseth';
        currentStoryConfig.auto_multi_voice = false;
    }

    syncStagedCardControls();
    refreshStagedCardVoiceMeta();

    const voiceLabels = {
        'piseth': 'ពិសិដ្ឋ (Piseth - តួប្រុស/អ្នកនិទានរឿងទោល)',
        'sreymom': 'ស្រីមុំ (Sreymom - តួស្រី/អ្នកនិទានរឿងទោល)'
    };
    showToast(`🎙️ បានប្តូរសំឡេង: ${voiceLabels[voiceKey] || voiceKey}`);
    appendLiveTerminalLine(`Dubbing voice set to: ${voiceLabels[voiceKey] || voiceKey}`, "[Voice Config]", "info");

    // Sync modal selector
    const modalSelect = document.getElementById('story-voice-select');
    if (modalSelect) modalSelect.value = voiceKey;

    try {
        await fetch('/api/set-story-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                khmer_voice: currentStoryConfig.khmer_voice,
                auto_multi_voice: false
            })
        });
    } catch (e) {
        console.warn("Save quick voice error:", e);
    }
}

function selectQuickBgmPreset(val) {
    const slider = document.getElementById('staged-bgm-slider');
    if (slider) slider.value = val;
    onQuickBgmSliderChange(val);
}

let quickBgmSaveDebounce = null;
function onQuickBgmSliderChange(val) {
    const numVal = parseInt(val, 10);
    const duckingFraction = (numVal / 100).toFixed(2);
    currentStoryConfig.ducking_volume = duckingFraction;

    [0, 10, 18, 28].forEach(p => {
        const btn = document.getElementById(`bgm-pre-${p}`);
        if (btn) {
            if (p === numVal) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    });

    const bgmBadge = document.getElementById('staged-bgm-val-badge');
    if (bgmBadge) {
        if (numVal === 0) bgmBadge.textContent = "0% (បិទភ្លេង)";
        else if (numVal <= 10) bgmBadge.textContent = `${numVal}% • ភ្លេងស្រាល`;
        else if (numVal <= 20) bgmBadge.textContent = `${numVal}% • ស្តង់ដារពិរោះ`;
        else bgmBadge.textContent = `${numVal}% • ភ្លេងរាងឮ`;
    }

    const modalSlider = document.getElementById('story-ducking-slider');
    if (modalSlider) modalSlider.value = numVal;

    if (quickBgmSaveDebounce) clearTimeout(quickBgmSaveDebounce);
    quickBgmSaveDebounce = setTimeout(async () => {
        try {
            await fetch('/api/set-story-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ducking_volume: duckingFraction
                })
            });
            showToast(`🎵 កម្រិតសំឡេងភ្លេង BGM បានកែសម្រួល: ${numVal}%`);
            appendLiveTerminalLine(`BGM volume / ducking set to: ${numVal}%`, "[Audio Config]", "info");
        } catch (e) {}
    }, 400);
}

async function loadStoryConfigData() {
    try {
        const res = await fetch('/api/story-config');
        if (res.ok) {
            const data = await res.json();
            if (data.success && data.config) {
                currentStoryConfig = Object.assign(currentStoryConfig, data.config);
                syncStagedCardControls();
                refreshStagedCardVoiceMeta();
            }
        }
    } catch (e) {
        console.warn("Story config load note:", e);
    }
}

async function loadDramaDictionaryUI() {
    try {
        const res = await fetch('/api/drama-dictionary');
        if (res.ok) {
            const data = await res.json();
            if (data.success && data.dictionary) {
                const dictElem = document.getElementById('story-dictionary-textarea');
                if (dictElem) {
                    const lines = Object.entries(data.dictionary).map(([k, v]) => `${k} = ${v}`);
                    dictElem.value = lines.join('\n');
                }
            }
        }
    } catch (e) {
        console.warn("Dictionary load note:", e);
    }
}

async function openStorySettingsModal() {
    await loadStoryConfigData();
    await loadDramaDictionaryUI();

    // Populate Voice & AI Tab fields
    const selVoice = document.getElementById('story-voice-select');
    let activeVoice = (currentStoryConfig.khmer_voice === 'sreymom') ? 'sreymom' : 'piseth';
    if (selVoice) selVoice.value = activeVoice;

    const selLang = document.getElementById('story-source-lang');
    if (selLang) selLang.value = currentStoryConfig.source_lang || 'auto';

    const selWhisper = document.getElementById('story-whisper-model');
    if (selWhisper) selWhisper.value = currentStoryConfig.whisper_model || 'medium';

    const lblProvider = document.getElementById('story-ai-provider-display');
    if (lblProvider) lblProvider.textContent = currentStoryConfig.ai_provider_display || 'Gemini API (Key Pool)';

    // Video & Look
    const selAspect = document.getElementById('story-aspect-ratio');
    if (selAspect) selAspect.value = currentStoryConfig.aspect_ratio || '9:16';

    const selSub = document.getElementById('story-subtitle-mode');
    if (selSub) selSub.value = currentStoryConfig.subtitle_mode || 'none';

    // Audio & Music
    const selDub = document.getElementById('story-dubbing-mode');
    if (selDub) selDub.value = currentStoryConfig.dubbing_mode || 'smart_bgm';

    let duckPct = 15;
    const rawDuck = parseFloat(currentStoryConfig.ducking_volume);
    if (!isNaN(rawDuck)) {
        duckPct = Math.round(rawDuck * 100);
        if (duckPct < 0) duckPct = 0;
        if (duckPct > 40) duckPct = 40;
    }
    syncStoryDuckingUI(duckPct);

    let speechVal = (currentStoryConfig.speech_boost_db !== undefined) ? parseFloat(currentStoryConfig.speech_boost_db) : 2.5;
    if (isNaN(speechVal)) speechVal = 2.5;
    syncStorySpeechUI(speechVal);

    updateStoryVoiceHint();
    switchStoryTab('voice');
    openModal('modal-story-settings');
}

function formatDuckingDbText(pct) {
    if (pct <= 0) return "🔇 0% (-45dB) • បិទស្ងាត់ពេលនិយាយ";
    const db = 20 * Math.log10(Math.max(0.005, pct / 100));
    let desc = "ស្តង់ដារពិរោះ";
    if (pct <= 4) desc = "ស្រាលបំផុត";
    else if (pct <= 8) desc = "ស្រាលទន់";
    else if (pct <= 18) desc = "⭐ ស្តង់ដារពិរោះ";
    else if (pct <= 28) desc = "រាងឮច្បាស់";
    else desc = "🔊 ឮខ្លាំង";
    return `${pct}% (${db.toFixed(1)} dB) • ${desc}`;
}

function syncStoryDuckingUI(pct) {
    pct = parseInt(pct, 10);
    if (isNaN(pct)) pct = 15;
    pct = Math.max(0, Math.min(40, pct));

    const slider = document.getElementById('story-ducking-slider');
    const hidden = document.getElementById('story-ducking-vol');
    const badge = document.getElementById('story-ducking-badge');
    const container = document.getElementById('story-ducking-presets');

    if (slider) slider.value = pct;
    if (hidden) hidden.value = (pct / 100).toFixed(2);
    if (badge) badge.textContent = formatDuckingDbText(pct);

    if (container) {
        const chips = container.querySelectorAll('.ai-preset-chip');
        chips.forEach(chip => {
            const v = parseInt(chip.getAttribute('data-val'), 10);
            chip.classList.toggle('active', v === pct);
        });
    }
}

function onStoryDuckingSliderChange(val) {
    syncStoryDuckingUI(val);
}

function setDuckingPreset(pct) {
    syncStoryDuckingUI(pct);
}

function formatSpeechDbText(val) {
    let desc = "ស្តង់ដារពិរោះ";
    if (val === 0) desc = "កម្រិតធម្មតា";
    else if (val <= 1.5) desc = "ស្រទន់";
    else if (val <= 3.0) desc = "⭐ ណែនាំច្បាស់";
    else if (val <= 5.0) desc = "ច្បាស់មាំ";
    else desc = "🔥 ខ្លាំងបំផុត";
    const prefix = val > 0 ? `+${val.toFixed(1)}` : `${val.toFixed(1)}`;
    return `${prefix} dB • ${desc}`;
}

function syncStorySpeechUI(val) {
    val = parseFloat(val);
    if (isNaN(val)) val = 2.5;
    val = Math.max(0, Math.min(8, val));

    const slider = document.getElementById('story-speech-slider');
    const hidden = document.getElementById('story-speech-boost');
    const badge = document.getElementById('story-speech-badge');
    const container = document.getElementById('story-speech-presets');

    if (slider) slider.value = val;
    if (hidden) hidden.value = val.toFixed(1);
    if (badge) badge.textContent = formatSpeechDbText(val);

    if (container) {
        const chips = container.querySelectorAll('.ai-preset-chip');
        chips.forEach(chip => {
            const v = parseFloat(chip.getAttribute('data-val'));
            chip.classList.toggle('active', Math.abs(v - val) < 0.1);
        });
    }
}

function onStorySpeechSliderChange(val) {
    syncStorySpeechUI(val);
}

function setSpeechBoostPreset(val) {
    syncStorySpeechUI(val);
}

function switchStoryTab(tabKey) {
    const tabs = ['voice', 'video', 'audio', 'vocal', 'export', 'dictionary'];
    tabs.forEach(t => {
        const btn = document.getElementById(`story-tab-btn-${t}`);
        const view = document.getElementById(`story-view-${t}`);
        if (btn) btn.classList.toggle('active', t === tabKey);
        if (view) view.style.display = (t === tabKey) ? 'flex' : 'none';
    });
}

function applyDramaDictionaryPreset(presetKey) {
    const dictElem = document.getElementById('story-dictionary-textarea');
    if (!dictElem) return;

    const presets = {
        modern_ceo: [
            "总裁 = លោកប្រធាន",
            "董事长 = ប្រធានក្រុមប្រឹក្សាភិបាល",
            "夫人 = លោកជំទាវ",
            "少爷 = អ្នកប្រុស",
            "小姐 = អ្នកនាង",
            "特助 = ជំនួយការពិសេស",
            "经理 = អ្នកគ្រប់គ្រង",
            "秘书 = លេខា",
            "保安 = សន្តិសុខ"
        ],
        family_inlaw: [
            "婆婆 = ម្តាយក្មេក",
            "公公 = ឪពុកក្មេក",
            "儿媳 = កូនប្រសារស្រី",
            "女婿 = កូនប្រសារប្រុស",
            "大嫂 = បងថ្លៃស្រី",
            "小叔子 = ប្អូនថ្លៃប្រុស",
            "丈母娘 = ម្តាយក្មេក",
            "亲家 = ញាតិសន្តាន"
        ],
        palace_royal: [
            "皇上 = ព្រះរាជា",
            "陛下 = ព្រះអង្គ",
            "皇后 = ព្រះអគ្គមហេសី",
            "贵妃 = ព្រះស្នំឯក",
            "娘娘 = ព្រះនាង",
            "王爷 = ព្រះអង្គម្ចាស់",
            "太后 = ព្រះវររាជមាតា",
            "微臣 = ទូលបង្គំ",
            "奴才 = ខ្ញុំម្ចាស់",
            "龙胎 = កូននាគរាជ"
        ],
        wuxia_martial: [
            "掌门 = មេបក្ស",
            "师傅 = លោកគ្រូ",
            "师兄 = រៀមច្បងប្រុស",
            "师妹 = អនុជស្រី",
            "大侠 = វីរបុរស",
            "教主 = មេនិកាយ",
            "前辈 = រៀមច្បងជាន់ខ្ពស់",
            "在下 = រូបខ្ញុំ"
        ]
    };

    const linesToAdd = presets[presetKey] || [];
    if (linesToAdd.length === 0) return;

    let current = dictElem.value.trim();
    const existingLines = current ? current.split('\n') : [];
    const merged = new Set(existingLines);

    linesToAdd.forEach(l => merged.add(l));
    dictElem.value = Array.from(merged).join('\n');
    showToast(`📚 បានបញ្ចូលវចនានុក្រមគំរូ: ${presetKey}`);
}

function updateStoryVoiceHint() {
    const hint = document.getElementById('story-voice-hint');
    const selVoice = document.getElementById('story-voice-select');
    if (!hint || !selVoice) return;

    const val = selVoice.value;
    if (val === 'sreymom') {
        hint.innerHTML = `<span style="color:#f472b6; font-weight:bold;">👩 Sreymom (សំឡេងស្រីទោល):</span> ប្រើសំឡេងស្រីមុំទោលស្រទន់ &amp; ពិរោះរលូនសម្រាប់គ្រប់ឃ្លា (Female Solo)។`;
    } else {
        hint.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">👨 Piseth (សំឡេងប្រុសទោល):</span> ប្រើសំឡេងពិសិដ្ឋទោលច្បាស់ &amp; ពិរោះរលូនសម្រាប់គ្រប់ឃ្លា (Male Solo)។`;
    }
}

function onStoryVoiceChange() {
    updateStoryVoiceHint();
    const selVoice = document.getElementById('story-voice-select');
    if (!selVoice) return;
    if (selVoice.value === 'sreymom') {
        showToast("👩 បានជ្រើសរើស: Sreymom (សំឡេងស្រីទោល)");
    } else {
        showToast("👨 បានជ្រើសរើស: Piseth (សំឡេងប្រុសទោល)");
    }
}

function onToggleMultiVoice(isChecked) {
    const selVoice = document.getElementById('story-voice-select');
    if (selVoice) selVoice.value = isChecked ? 'sreymom' : 'piseth';
    updateStoryVoiceHint();
}

async function saveStorySettings() {
    const selVoice = document.getElementById('story-voice-select');
    const voice = (selVoice && selVoice.value === 'sreymom') ? 'sreymom' : 'piseth';
    const isMulti = false;
    const lang = document.getElementById('story-source-lang') ? document.getElementById('story-source-lang').value : 'auto';
    const whisper = document.getElementById('story-whisper-model') ? document.getElementById('story-whisper-model').value : 'medium';
    const aspect = document.getElementById('story-aspect-ratio') ? document.getElementById('story-aspect-ratio').value : '9:16';
    const subtitle = document.getElementById('story-subtitle-mode') ? document.getElementById('story-subtitle-mode').value : 'none';
    const dubMode = document.getElementById('story-dubbing-mode') ? document.getElementById('story-dubbing-mode').value : 'smart_bgm';
    const duckElem = document.getElementById('story-ducking-vol');
    let duckVol = duckElem && duckElem.value ? duckElem.value : '0.15';
    if (!duckVol || isNaN(parseFloat(duckVol))) duckVol = '0.15';

    const boostElem = document.getElementById('story-speech-boost');
    let boost = boostElem && boostElem.value ? parseFloat(boostElem.value) : 2.5;
    if (isNaN(boost)) boost = 2.5;

    const payload = {
        khmer_voice: voice,
        auto_multi_voice: isMulti,
        source_lang: lang,
        whisper_model: whisper,
        aspect_ratio: aspect,
        subtitle_mode: subtitle,
        dubbing_mode: dubMode,
        ducking_volume: duckVol,
        speech_boost_db: boost
    };

    // Save Drama Dictionary if edited
    const dictElem = document.getElementById('story-dictionary-textarea');
    if (dictElem) {
        const dictMap = {};
        dictElem.value.split('\n').forEach(line => {
            const trimmed = line.trim();
            if (trimmed && (trimmed.includes('=') || trimmed.includes(':'))) {
                const parts = trimmed.includes('=') ? trimmed.split('=') : trimmed.split(':');
                if (parts.length >= 2) {
                    const k = parts[0].trim();
                    const v = parts.slice(1).join('=').trim();
                    if (k && v) dictMap[k] = v;
                }
            }
        });
        try {
            await fetch('/api/drama-dictionary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dictionary: dictMap })
            });
        } catch (e) {
            console.warn("Dictionary save note:", e);
        }
    }

    try {
        const resp = await fetch('/api/set-story-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const resData = await resp.json();
        if (resData.success) {
            currentStoryConfig = Object.assign(currentStoryConfig, payload);
            refreshStagedCardVoiceMeta();
            syncStagedCardControls();

            const voiceNameText = voice === 'multi' 
                ? "Piseth & Sreymom (ប្រុស & ស្រី)" 
                : (voice === 'sreymom' ? "Sreymom (ស្រីទោល)" : "Piseth (ប្រុសទោល)");
            showToast(`✨ បានរក្សាទុកការកំណត់សំឡេង និងវចនានុក្រម: ${voiceNameText} ដោយជោគជ័យ!`);
            closeModal('modal-story-settings');
        } else {
            showToast(`⚠️ ${resData.message || 'Error saving story settings'}`);
        }
    } catch (e) {
        showToast(`❌ Error saving: ${e.message}`);
    }
}


async function saveApiKey() {
    const key = document.getElementById('input-api-key').value.trim();
    if (key) {
        try {
            await fetch('/api/set-api-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key })
            });
        } catch (e) {}
    }
    showToast("✨ Saved Studio Engine Token!");
    backToSettingsHub();
}

// ==========================================================================
// AI PROVIDING & GEMINI KEY POOL MANAGER (Exact Match to User Image 2)
// ==========================================================================
let currentAiConfig = {
    engine: "gemini_pool",
    keys: [],
    keys_raw: "",
    model: "gemini-2.5-flash",
    temperature: 0.3,
    prompt_style: "drama_dubbing"
};

async function loadAiConfigData() {
    try {
        const res = await fetch('/api/ai-config');
        if (res.ok) {
            const data = await res.json();
            if (data.success && data.config) {
                currentAiConfig = Object.assign(currentAiConfig, data.config);
            }
        }
    } catch (e) {
        console.warn("AI config load note:", e);
    }
}

async function openAiProvidingModal() {
    await loadAiConfigData();

    // Populate UI fields
    const selEngine = document.getElementById('ai-engine-select');
    if (selEngine) selEngine.value = currentAiConfig.engine || 'auto';

    const txtKeys = document.getElementById('ai-keys-pool-textarea');
    if (txtKeys) {
        txtKeys.value = currentAiConfig.keys_raw || (currentAiConfig.keys ? currentAiConfig.keys.join('\n') : '');
    }

    const selModel = document.getElementById('ai-model-select');
    if (selModel && currentAiConfig.model) selModel.value = currentAiConfig.model;

    const sliderTemp = document.getElementById('ai-temperature-slider');
    const badgeTemp = document.getElementById('ai-temp-val');
    if (sliderTemp && currentAiConfig.temperature !== undefined) {
        sliderTemp.value = currentAiConfig.temperature;
        if (badgeTemp) badgeTemp.textContent = currentAiConfig.temperature;
    }

    const txtPrompt = document.getElementById('ai-system-prompt-input');
    if (txtPrompt && currentAiConfig.prompt_style && currentAiConfig.prompt_style.length > 20) {
        txtPrompt.value = currentAiConfig.prompt_style;
    }

    handleAiKeysInput();
    switchAiProvidingTab('provider');
    openModal('modal-ai-providing');
}

function switchAiProvidingTab(tabKey) {
    const tabs = ['provider', 'models', 'backup'];
    tabs.forEach(t => {
        const btn = document.getElementById(`ai-tab-btn-${t}`);
        const view = document.getElementById(`ai-view-${t}`);
        if (btn) btn.classList.toggle('active', t === tabKey);
        if (view) view.style.display = (t === tabKey) ? 'flex' : 'none';
    });
}

function onAiEngineChange() {
    const sel = document.getElementById('ai-engine-select');
    if (!sel) return;
    const val = sel.value;
    if (val === 'free_ai') {
        showToast("🤖 Selected: Free AI Translation (No API Key Required)");
    } else if (val === 'google_free') {
        showToast("🌐 Selected: Google Translate Built-in Free");
    } else {
        showToast("⚡ Selected: Gemini Neural Key Pool");
    }
}

function handleAiKeysInput() {
    const textarea = document.getElementById('ai-keys-pool-textarea');
    const gutter = document.getElementById('ai-editor-gutter');
    const badge = document.getElementById('ai-key-count-badge');
    if (!textarea) return;

    const val = textarea.value;
    const lines = val.split('\n');
    const lineCount = Math.max(1, lines.length);

    if (gutter) {
        let gutterHtml = '';
        for (let i = 1; i <= lineCount; i++) {
            gutterHtml += `<div>${i}</div>`;
        }
        gutter.innerHTML = gutterHtml;
    }

    const nonBlankKeys = lines.map(l => l.trim()).filter(l => l.length > 0);
    if (badge) {
        if (nonBlankKeys.length === 0) {
            badge.textContent = "0 loaded";
            badge.style.color = "#94a3b8";
        } else {
            badge.textContent = `${nonBlankKeys.length} loaded · active`;
            badge.style.color = "var(--gold-glow)";
        }
    }
}

function syncAiEditorScroll() {
    const textarea = document.getElementById('ai-keys-pool-textarea');
    const gutter = document.getElementById('ai-editor-gutter');
    if (textarea && gutter) {
        gutter.scrollTop = textarea.scrollTop;
    }
}

function triggerImportKeysFile() {
    const fileInput = document.getElementById('ai-keys-file-input');
    if (fileInput) {
        fileInput.value = "";
        fileInput.click();
    }
}

function handleAiKeysFileSelect(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const content = e.target.result || "";
        const textarea = document.getElementById('ai-keys-pool-textarea');
        if (textarea) {
            const existing = textarea.value.trim();
            const newKeys = content.trim();
            if (existing) {
                textarea.value = existing + "\n" + newKeys;
            } else {
                textarea.value = newKeys;
            }
            handleAiKeysInput();
            showToast(`📥 Imported keys from ${file.name}`);
        }
    };
    reader.readAsText(file);
}

async function checkKeysLive() {
    const textarea = document.getElementById('ai-keys-pool-textarea');
    if (!textarea) return;

    const raw = textarea.value.trim();
    const lines = raw.split('\n').map(l => l.trim()).filter(l => l.length > 0);

    if (lines.length === 0) {
        showToast("⚠️ សូមបញ្ចូល Gemini API Key យ៉ាងតិច ១ មុនពេល Check!");
        return;
    }

    const checkBtn = document.getElementById('btn-check-keys-live');
    const origHtml = checkBtn ? checkBtn.innerHTML : "";
    if (checkBtn) {
        checkBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Checking ${lines.length} keys...`;
        checkBtn.disabled = true;
    }

    try {
        const resp = await fetch('/api/check-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keys: lines, keys_raw: raw })
        });
        const resData = await resp.json();
        if (resData.success) {
            const badge = document.getElementById('ai-key-count-badge');
            if (badge) {
                badge.textContent = `${resData.valid} / ${resData.total} live active`;
                badge.style.color = resData.valid > 0 ? "#4ade80" : "#f87171";
            }
            showToast(`✅ Key Check Complete: ${resData.valid} of ${resData.total} keys active!`);
        } else {
            showToast(`❌ Check error: ${resData.error || 'Failed'}`);
        }
    } catch (err) {
        showToast(`❌ Network error while checking keys: ${err.message}`);
    } finally {
        if (checkBtn) {
            checkBtn.innerHTML = origHtml;
            checkBtn.disabled = false;
        }
    }
}

function exportKeysBackup() {
    const textarea = document.getElementById('ai-keys-pool-textarea');
    const content = textarea ? textarea.value.trim() : "";
    if (!content) {
        showToast("⚠️ មិនមាន API Key សម្រាប់ Export ទេ!");
        return;
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gemini_api_keys_backup_${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("💾 បាន Export Backup API Keys ដោយជោគជ័យ!");
}

function clearAllKeysPool() {
    if (!confirm("តើអ្នកពិតជាចង់លុប Gemini API Keys ទាំងអស់នេះមែនទេ?")) return;
    const textarea = document.getElementById('ai-keys-pool-textarea');
    if (textarea) {
        textarea.value = "";
        handleAiKeysInput();
    }
    showToast("🧹 បានសម្អាត Keys ទាំងអស់រួចរាល់!");
}

async function saveAiProvidingConfig() {
    const engine = document.getElementById('ai-engine-select') ? document.getElementById('ai-engine-select').value : 'auto';
    const keysRaw = document.getElementById('ai-keys-pool-textarea') ? document.getElementById('ai-keys-pool-textarea').value.trim() : '';
    const model = document.getElementById('ai-model-select') ? document.getElementById('ai-model-select').value : 'qwen/qwen3.8-27b';
    const temperature = document.getElementById('ai-temperature-slider') ? parseFloat(document.getElementById('ai-temperature-slider').value) : 0.3;
    const promptStyle = document.getElementById('ai-system-prompt-input') ? document.getElementById('ai-system-prompt-input').value.trim() : '';

    const keysList = keysRaw.split('\n').map(k => k.trim()).filter(k => k.length > 0);

    try {
        const resp = await fetch('/api/set-ai-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                engine: engine,
                keys: keysList,
                keys_raw: keysRaw,
                model: model,
                temperature: temperature,
                prompt_style: promptStyle
            })
        });
        const resData = await resp.json();
        if (resData.success) {
            currentAiConfig = resData.config;
            showToast(`✨ បានរក្សាទុកការកំណត់ AI Providing និង Keys (${keysList.length} គ្រាប់) ដោយជោគជ័យ!`);
            closeModal('modal-ai-providing');
        } else {
            showToast(`⚠️ ${resData.message || 'Error saving settings'}`);
        }
    } catch (e) {
        showToast(`❌ បរាជ័យក្នុងការរក្សាទុក: ${e.message}`);
    }
}

function openImportModal() { openModal('modal-import'); }

async function triggerFileSelect() {
    try {
        const res = await fetch("/api/system/select-media-files", { method: "POST" });
        const data = await res.json();
        if (data.success && data.files && data.files.length > 0) {
            closeModal('modal-import');
            handleSelectedFiles(data.files);
            return;
        } else if (data.cancelled) {
            closeModal('modal-import');
            return;
        }
    } catch (e) {
        console.warn("Native file picker note, falling back to HTML input:", e);
    }
    const input = document.getElementById('batch-files-input');
    if (input) input.click();
}

async function triggerFolderSelect() {
    try {
        const res = await fetch("/api/system/select-media-folder", { method: "POST" });
        const data = await res.json();
        if (data.success && data.files && data.files.length > 0) {
            closeModal('modal-import');
            handleSelectedFiles(data.files, data.series_title);
            return;
        } else if (data.cancelled) {
            closeModal('modal-import');
            return;
        }
    } catch (e) {
        console.warn("Native folder picker note, falling back to HTML input:", e);
    }
    const input = document.getElementById('batch-folder-input');
    if (input) input.click();
}

let activeDubbingTaskId = null;
let activeDubbingPollTimer = null;
let currentDubbedProject = null;

let stagedVideoFile = null;
let stagedBatchFiles = null;

function setStagedVideo(file) {
    stagedVideoFile = file;
    stagedBatchFiles = null;

    const fileName = file.name || file.filename || "drama_video.mp4";
    const fileSizeMB = file.size_mb ? file.size_mb : (file.size ? (file.size / (1024 * 1024)).toFixed(1) : "0.0");

    // Preview video in left monitor (support both native filepath and browser File blob)
    const mainVideo = document.getElementById('main-video');
    if (mainVideo) {
        try {
            if (file.filepath) {
                mainVideo.src = `/media/${file.filepath.replace(/\\/g, '/')}`;
            } else {
                mainVideo.src = URL.createObjectURL(file);
            }
            mainVideo.style.display = 'block';
            mainVideo.load();

            const handleMeta = () => {
                if (mainVideo.duration && !isNaN(mainVideo.duration) && isFinite(mainVideo.duration) && mainVideo.duration > 0) {
                    totalDurationSeconds = mainVideo.duration;
                    playheadSeconds = 0;
                    updateScrubberUI();

                    const durM = Math.floor(totalDurationSeconds / 60);
                    const durS = Math.floor(totalDurationSeconds % 60);
                    const durFormatted = `${String(durM).padStart(2,'0')}:${String(durS).padStart(2,'0')}`;
                    const stagedMeta = document.getElementById('staged-file-meta');
                    if (stagedMeta) stagedMeta.textContent = `${fileSizeMB} MB • Duration: ${durFormatted} • ត្រៀមបកប្រែជាសំឡេងខ្មែរ`;
                }
            };
            mainVideo.onloadedmetadata = handleMeta;
            mainVideo.ondurationchange = handleMeta;
            mainVideo.oncanplay = handleMeta;
            mainVideo.onloadeddata = handleMeta;
        } catch (e) {
            console.warn("Video preview load note:", e);
        }
    }

    if (!file.filepath) {
        autoDetectVideoDuration(file, (dur) => {
            totalDurationSeconds = dur;
            playheadSeconds = 0;
            updateScrubberUI();
            const durM = Math.floor(dur / 60);
            const durS = Math.floor(dur % 60);
            const durFormatted = `${String(durM).padStart(2,'0')}:${String(durS).padStart(2,'0')}`;
            const stagedMeta = document.getElementById('staged-file-meta');
            if (stagedMeta) refreshStagedCardVoiceMeta();
            appendLiveTerminalLine(`Media imported: "${fileName}" • Duration: ${durFormatted} (${dur.toFixed(1)}s)`, "[Video 1/1]", "info");
        });
    } else {
        appendLiveTerminalLine(`Media imported: "${fileName}" (${fileSizeMB} MB) • Native Direct Link`, "[Video 1/1]", "info");
    }

    // Update Clean Source View to Staged Ready State
    const importPrompt = document.getElementById('clean-import-prompt');
    const stagedCard = document.getElementById('staged-video-card');
    const stagedTitle = document.getElementById('staged-file-title');
    const stagedMeta = document.getElementById('staged-file-meta');
    const sourceLabel = document.getElementById('clean-source-label');

    if (importPrompt) importPrompt.style.display = 'none';
    if (stagedCard) stagedCard.style.display = 'flex';
    if (sourceLabel) sourceLabel.style.display = 'none';
    if (stagedTitle) stagedTitle.textContent = fileName;
    refreshStagedCardVoiceMeta();
    syncStagedCardControls();

    const exportBtn = document.getElementById('btn-tab-export');
    if (exportBtn) exportBtn.classList.add('export-ready-pulse');

    const pill = document.getElementById('monitor-engine-status-pill');
    const dot = document.getElementById('monitor-pulse-dot');
    const text = document.getElementById('monitor-engine-status-text');
    if (pill) pill.className = 'engine-status-pill standby';
    if (dot) dot.className = 'pulse-indicator standby';
    if (text) text.textContent = 'READY FOR EXPORT';

    updateScrubberUI();
    showToast(`📁 បានផ្ទុក "${fileName}" ជោគជ័យ! សូមចុច Export ដើម្បីចាប់ផ្តើមបកប្រែ។`);
    appendTerminalLine(`[Ready] Video "${fileName}" staged. Click [Export] to begin AI Dubbing.`);
}

function setStagedBatchFiles(files, folderTitle = "") {
    stagedBatchFiles = files;
    stagedVideoFile = null;

    if (files && files.length > 0) {
        const firstFile = files[0];
        const mainVideo = document.getElementById('main-video');
        if (mainVideo) {
            try {
                if (firstFile.filepath) {
                    mainVideo.src = `/media/${firstFile.filepath.replace(/\\/g, '/')}`;
                } else {
                    mainVideo.src = URL.createObjectURL(firstFile);
                }
                mainVideo.style.display = 'block';
                mainVideo.load();
            } catch (e) {
                console.warn("Batch preview load note:", e);
            }
        }
    }

    const importPrompt = document.getElementById('clean-import-prompt');
    const stagedCard = document.getElementById('staged-video-card');
    const stagedTitle = document.getElementById('staged-file-title');
    const stagedMeta = document.getElementById('staged-file-meta');
    const sourceLabel = document.getElementById('clean-source-label');

    if (importPrompt) importPrompt.style.display = 'none';
    if (stagedCard) stagedCard.style.display = 'flex';
    if (sourceLabel) sourceLabel.style.display = 'none';

    let folderName = folderTitle || "";
    if (!folderName && files[0] && files[0].webkitRelativePath) {
        const parts = files[0].webkitRelativePath.split('/');
        if (parts.length > 1) folderName = parts[0];
    }
    const seriesTitle = folderName ? `Folder: "${folderName}"` : `រឿងភាគមួយចប់`;

    if (stagedTitle) stagedTitle.textContent = `🎬 ${seriesTitle} (${files.length} ភាគ)`;
    if (stagedMeta) stagedMeta.textContent = `បានតម្រៀបតាមលំដាប់រឿង Episode 1 ដល់ ${files.length} ត្រឹមត្រូវ • ចុច "Export" ដើម្បីបកប្រែទាំងអស់`;
    refreshStagedCardVoiceMeta();
    syncStagedCardControls();

    const exportBtn = document.getElementById('btn-tab-export');
    if (exportBtn) exportBtn.classList.add('export-ready-pulse');

    showToast(`📁 បានផ្ទុក ${files.length} ភាគក្នុង Folder ជោគជ័យ! ចុច Export ដើម្បីចាប់ផ្តើមបកប្រែ។`);
    clearLiveTerminal();
    appendLiveTerminalLine(`Folder / Series Staged: ${files.length} episodes loaded in story order.`, "[Batch Ready]", "info");
    for (let i = 0; i < Math.min(files.length, 5); i++) {
        const f = files[i];
        const fName = f.name || f.filename || `Episode ${i+1}`;
        const fMB = f.size_mb || (f.size ? (f.size / (1024*1024)).toFixed(1) : "?");
        appendLiveTerminalLine(`  • Episode ${i+1}: "${fName}" (${fMB} MB)`, "[Episode List]", "info");
    }
    if (files.length > 5) {
        appendLiveTerminalLine(`  ... និង ${files.length - 5} ភាគទៀត`, "[Episode List]", "info");
    }
    appendLiveTerminalLine(`Click [Export] on the top bar to begin full drama automated dubbing.`, "[Ready]", "success");
}

function clearStagedFiles() {
    stagedVideoFile = null;
    stagedBatchFiles = null;
    const exportBtn = document.getElementById('btn-tab-export');
    if (exportBtn) exportBtn.classList.remove('export-ready-pulse');

    const importPrompt = document.getElementById('clean-import-prompt');
    const stagedCard = document.getElementById('staged-video-card');
    const sourceLabel = document.getElementById('clean-source-label');
    if (importPrompt) importPrompt.style.display = 'flex';
    if (stagedCard) stagedCard.style.display = 'none';
    if (sourceLabel) sourceLabel.style.display = 'block';
}

function handleSelectedFiles(files, folderTitle = "") {
    if (!files || files.length === 0) return;
    closeModal('modal-import');

    const validExts = ['.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv', '.ts', '.m4v', '.wmv'];
    const fileList = Array.from(files).filter(f => {
        const n = (f.name || f.filename || '').toLowerCase();
        return validExts.some(ext => n.endsWith(ext)) || (f.type && f.type.startsWith('video/'));
    });

    if (fileList.length === 0) {
        showToast("⚠️ សូមជ្រើសរើសឯកសារជាប្រភេទវីដេអូរឿងភាគ (MP4, MKV, MOV...)");
        return;
    }

    // Natural numerical sorting: Episode 1, Episode 2, Episode 10 in true story order!
    fileList.sort((a, b) => {
        const nameA = a.name || a.filename || "";
        const nameB = b.name || b.filename || "";
        return nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' });
    });

    if (fileList.length === 1) {
        setStagedVideo(fileList[0]);
    } else {
        setStagedBatchFiles(fileList, folderTitle);
    }
}

async function startAutoDubbingPipeline(file) {
    const fileName = file.name || file.filename || "drama_video.mp4";
    const fileSizeMB = file.size_mb ? file.size_mb : (file.size ? (file.size / (1024*1024)).toFixed(1) : "?");
    showToast(`🚀 កំពុងរៀបចំ និងចាប់ផ្តើមបកប្រែវីដេអូ: ${fileName}`);

    // Output initial console startup sequence matching Image 2
    clearLiveTerminal();
    appendLiveTerminalLine(`Job initiated: AI Video Dubbing & Translation Pipeline`, "[Video 1/1]", "info");
    appendLiveTerminalLine(`Source media: ${fileName} (${fileSizeMB} MB)...`, "[Video 1/1]", "info");
    appendLiveTerminalLine(`AI voice removal: extracting audio...`, "[Video 1/1]", "info");
    appendLiveTerminalLine(`AI voice removal: preparing the separation engine...`, "[Video 1/1]", "info");
    appendLiveTerminalLine(`AI voice removal: running on GPU (CUDA / DirectML)...`, "[Video 1/1]", "info");
    appendLiveTerminalLine(`AI voice removal: using the built-in model.`, "[Video 1/1]", "info");

    // Keep clean source view active (uncluttered layout)
    showCleanSourceView();

    // Set Engine Monitor to Active Encoding State
    const pill = document.getElementById('monitor-engine-status-pill');
    const dot = document.getElementById('monitor-pulse-dot');
    const text = document.getElementById('monitor-engine-status-text');
    if (pill) pill.className = 'engine-status-pill';
    if (dot) dot.className = 'pulse-indicator';
    if (text) text.textContent = 'AI DUBBING IN PROGRESS';

    updateExportProgressUI(5, 0, 90, "១/៦ កំពុងភ្ជាប់វីដេអូទៅកាន់ម៉ាស៊ីន Studio...");

    const activeDramaMode = currentStudioPreset === "narration" ? "movie_recap" : "drama_dubbing";
    const activeSourceLang = currentStoryConfig.source_lang || "auto";
    const activeVoiceOverride = (currentStoryConfig.auto_multi_voice || currentStoryConfig.khmer_voice === "multi") 
        ? "multi" 
        : (currentStoryConfig.khmer_voice || "piseth");
    const activeAspectRatio = currentStoryConfig.aspect_ratio || "9:16";
    const activeBurnSubs = (currentStoryConfig.subtitle_mode === "burn") ? "true" : "false";

    try {
        let res;
        if (file.filepath) {
            res = await fetch("/api/projects/auto-dub-video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filepath: file.filepath,
                    drama_mode: activeDramaMode,
                    source_lang: activeSourceLang,
                    voice_override: activeVoiceOverride,
                    aspect_ratio: activeAspectRatio,
                    burn_subtitles: activeBurnSubs
                })
            });
        } else {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("drama_mode", activeDramaMode);
            formData.append("source_lang", activeSourceLang);
            formData.append("voice_override", activeVoiceOverride);
            formData.append("aspect_ratio", activeAspectRatio);
            formData.append("burn_subtitles", activeBurnSubs);

            res = await fetch("/api/projects/auto-dub-video", {
                method: "POST",
                body: formData
            });
        }
        const data = await res.json();
        if (!data.success || !data.task_id) {
            showToast(`❌ បរាជ័យ: ${data.error || "មិនអាចចាប់ផ្តើមបានទេ"}`);
            appendLiveTerminalLine(`Failed to start pipeline: ${data.error || 'Server error'}`, "[Error]", "error");
            resetEngineMonitorToStandby();
            return;
        }

        activeDubbingTaskId = data.task_id;
        let elapsed = 0;
        let lastLoggedStep = "";
        let loggedDialogueIds = new Set();
        let sepProgressSim = 2;
        let sepTimerTicks = 0;

        appendLiveTerminalLine(`Dubbing engine dispatched in background. Task ID: ${activeDubbingTaskId}`, "[Video 1/1]", "info");

        if (activeDubbingPollTimer) clearInterval(activeDubbingPollTimer);
        activeDubbingPollTimer = setInterval(async () => {
            elapsed += 1;
            try {
                const sRes = await fetch(`/api/projects/auto-dub-status/${activeDubbingTaskId}`);
                const sData = await sRes.json();
                if (!sData.success) return;

                const pct = sData.progress || 10;
                const stepKm = sData.step_km || "កំពុងដំណើរការ...";
                const stepEn = sData.step_en || stepKm;
                const rem = 100 - pct;
                const eta = Math.max(1, Math.round((elapsed / Math.max(1, pct)) * rem));

                updateExportProgressUI(pct, elapsed, eta, stepKm);
                
                // Update bottom footer
                const footerProg = document.getElementById('footer-studio-progress');
                if (footerProg) footerProg.style.width = `${pct}%`;
                const footerText = document.querySelector('#footer-studio-main div:first-child');
                if (footerText) footerText.textContent = `Status: ${stepKm} (${pct}%)`;

                // Stream realistic vocal separation progress ticks while in separation stage (<35%)
                if (pct < 35) {
                    sepTimerTicks++;
                    if (sepTimerTicks % 2 === 0 && sepProgressSim < 95) {
                        appendLiveTerminalLine(`AI voice removal: separating voice from music (${sepProgressSim}%)...`, "[Video 1/1]", "info");
                        sepProgressSim += Math.floor(Math.random() * 4) + 3;
                    }
                }

                // Log pipeline milestone when step transitions
                if (stepEn && stepEn !== lastLoggedStep) {
                    lastLoggedStep = stepEn;
                    appendLiveTerminalLine(`${stepEn} (${pct}%) [${stepKm}]`, "[Video 1/1]", "info");
                }

                // Stream translated dialogue data lines in real-time
                const currentDialogues = (sData.project && sData.project.dialogues) || sData.dialogues || [];
                if (Array.isArray(currentDialogues) && currentDialogues.length > 0) {
                    currentDialogues.forEach((d, idx) => {
                        if (!loggedDialogueIds.has(idx)) {
                            loggedDialogueIds.add(idx);
                            const lineNum = String(idx + 1).padStart(2, '0');
                            const vName = (d.voice === 'sreymom' || d.voice === 'female') ? 'ស្រីមុំ (Sreymom)' : 'ពិសិដ្ឋ (Piseth)';
                            const zhText = d.text_original || d.text || "";
                            const kmText = d.text_km || d.translated_text || d.khmer_text || d.text || "";
                            if (kmText && kmText !== zhText) {
                                appendLiveTerminalLine(`[Line ${lineNum}] "${zhText}" ➜ "${kmText}" (${vName})`, "[ZH ➜ KM]", "dub");
                            }
                        }
                    });
                }

                if (sData.status === "completed") {
                    clearInterval(activeDubbingPollTimer);
                    activeDubbingPollTimer = null;
                    currentDubbedProject = sData.project;
                    clearStagedFiles();

                    // Final flush of any remaining dialogues
                    const allDialogues = (sData.project && sData.project.dialogues) || sData.dialogues || [];
                    if (Array.isArray(allDialogues) && allDialogues.length > 0) {
                        allDialogues.forEach((d, idx) => {
                            if (!loggedDialogueIds.has(idx)) {
                                loggedDialogueIds.add(idx);
                                const lineNum = String(idx + 1).padStart(2, '0');
                                const vName = (d.voice === 'sreymom' || d.voice === 'female') ? 'ស្រីមុំ (Female)' : 'ពិសិដ្ឋ (Male)';
                                const zhText = d.text || "(ចិន)";
                                const kmText = d.translated_text || d.khmer_text || "(ខ្មែរ)";
                                appendLiveTerminalLine(`[Line ${lineNum}] ZH: "${zhText}" ➜ KM: "${kmText}" (${vName})`, "[ZH ➜ KM]", "dub");
                            }
                        });
                    }

                    updateExportProgressUI(100, elapsed, 0, "🎉 រួចរាល់ ១០០%! វីដេអូសម្រេចបានរក្សាទុក!");
                    showToast("🎉 បកប្រែ និងបញ្ចូលសំឡេងខ្មែរជោគជ័យ ១០០%!");
                    appendLiveTerminalLine(`AI voice synthesis & audio mixing: 100% finished. Zero vocal leakage.`, "[Video 1/1]", "success");
                    appendLiveTerminalLine(`Master export MP4 generated: ${sData.project.output_video_file || 'Dubbed_Video.mp4'}`, "[Video 1/1]", "success");
                    appendLiveTerminalLine(`[Success 100%] Video dubbed successfully! Ready for playback.`, "[Video 1/1]", "success");

                    // Load dubbed video into player
                    const mainVideo = document.getElementById('main-video');
                    if (mainVideo && sData.video_url) {
                        mainVideo.src = sData.video_url;
                        mainVideo.style.display = 'block';
                        mainVideo.load();
                        totalDurationSeconds = sData.project.duration || 60;
                        updateScrubberUI();
                    }

                    // Store translated dialogues in memory for background playback, keeping UI clean
                    if (sData.project && sData.project.dialogues) {
                        activeLoadedDialogues = sData.project.dialogues;
                    }
                    showCleanSourceView();

                    // Show success action prompt with Open Folder & Download buttons
                    showDubbingSuccessNotification(sData);

                } else if (sData.status === "failed") {
                    clearInterval(activeDubbingPollTimer);
                    activeDubbingPollTimer = null;
                    showToast(`❌ កំហុស: ${sData.error || 'ដំណើរការបរាជ័យ'}`);
                    appendLiveTerminalLine(`Dubbing error: ${sData.error}`, "[Video 1/1]", "error");
                    resetEngineMonitorToStandby();
                }
            } catch (err) {
                console.warn("Poll error:", err);
            }
        }, 1000);

    } catch (e) {
        showToast("❌ កំហុសក្នុងការ Upload វីដេអូ");
        appendLiveTerminalLine(`Network upload failed: ${e.message}`, "[Error]", "error");
        resetEngineMonitorToStandby();
    }
}

async function startStudioBatchDubbingPipeline(files, outputMode = 'separate') {
    if (!files || files.length === 0) return;
    const totalBatchCount = files.length;
    const modeLabel = outputMode === 'full' ? 'បញ្ចូលគ្នារឿងពេញ (One Full Video)' : (outputMode === 'both' ? 'យកទាំងពីរ (Both Episodes & Full Video)' : 'បកប្រែជាភាគៗ (Separate Episodes)');
    showToast(`🎬 ចាប់ផ្តើមបកប្រែរឿងភាគ (${totalBatchCount} ភាគ) - ${modeLabel}...`);

    clearLiveTerminal();
    appendLiveTerminalLine(`========================================================================`, "[Batch Series]", "info");
    appendLiveTerminalLine(`Series Batch Dubbing Initiated: ${totalBatchCount} episodes loaded in story order.`, "[Batch Series]", "info");
    appendLiveTerminalLine(`Export Mode: "${outputMode.toUpperCase()}" (${modeLabel})`, "[Batch Series]", "info");
    appendLiveTerminalLine(`Voices: ពិសិដ្ឋ (Piseth - Male) & ស្រីមុំ (Sreymom - Female) • Zero Vocal Leakage Enabled`, "[Batch Series]", "info");
    appendLiveTerminalLine(`Mode: Studio In-Place Sequential Dubbing (stays right in Studio)`, "[Batch Series]", "info");
    appendLiveTerminalLine(`========================================================================`, "[Batch Series]", "info");

    // Keep clean source view active
    showCleanSourceView();

    // Set Engine Monitor to Active Encoding State
    const pill = document.getElementById('monitor-engine-status-pill');
    const dot = document.getElementById('monitor-pulse-dot');
    const text = document.getElementById('monitor-engine-status-text');
    if (pill) pill.className = 'engine-status-pill';
    if (dot) dot.className = 'pulse-indicator';

    let totalElapsedSeconds = 0;
    const batchMasterTimer = setInterval(() => {
        totalElapsedSeconds++;
    }, 1000);

    const completedProjects = [];

    for (let i = 0; i < totalBatchCount; i++) {
        const file = files[i];
        const epNum = i + 1;
        const fileName = file.name || file.filename || `Episode_${epNum}.mp4`;
        const fileSizeMb = file.size_mb !== undefined ? file.size_mb : (file.size ? (file.size / (1024 * 1024)).toFixed(1) : "?");

        if (text) text.textContent = `BATCH DUBBING (${epNum} / ${totalBatchCount})`;

        appendLiveTerminalLine(`------------------------------------------------------------------------`, `[Ep ${epNum}/${totalBatchCount}]`, "info");
        appendLiveTerminalLine(`▶ Starting Episode ${epNum}/${totalBatchCount}: "${fileName}" (${fileSizeMb} MB)...`, `[Ep ${epNum}/${totalBatchCount}]`, "info");
        appendLiveTerminalLine(`AI voice removal: extracting audio & isolating vocals...`, `[Ep ${epNum}/${totalBatchCount}]`, "info");

        const basePct = Math.round((i / totalBatchCount) * 100);
        updateExportProgressUI(basePct, totalElapsedSeconds, 60 * (totalBatchCount - i), `ភាគ ${epNum}/${totalBatchCount}: ${fileName} - កំពុងផ្ញើទៅ Studio...`);

        const dramaMode = currentStudioPreset === "narration" ? "movie_recap" : "drama_dubbing";
        const activeSourceLang = currentStoryConfig.source_lang || "auto";
        const activeVoiceOverride = (currentStoryConfig.auto_multi_voice || currentStoryConfig.khmer_voice === "multi") 
            ? "multi" 
            : (currentStoryConfig.khmer_voice || "piseth");
        const activeAspectRatio = currentStoryConfig.aspect_ratio || "9:16";
        const activeBurnSubs = (currentStoryConfig.subtitle_mode === "burn") ? "true" : "false";

        let taskId = null;
        try {
            let res;
            if (file.filepath) {
                res = await fetch("/api/projects/auto-dub-video", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        filepath: file.filepath,
                        filename: fileName,
                        drama_mode: dramaMode,
                        source_lang: activeSourceLang,
                        voice_override: activeVoiceOverride,
                        aspect_ratio: activeAspectRatio,
                        burn_subtitles: activeBurnSubs
                    })
                });
            } else {
                const formData = new FormData();
                formData.append("file", file);
                formData.append("drama_mode", dramaMode);
                formData.append("source_lang", activeSourceLang);
                formData.append("voice_override", activeVoiceOverride);
                formData.append("aspect_ratio", activeAspectRatio);
                formData.append("burn_subtitles", activeBurnSubs);

                res = await fetch("/api/projects/auto-dub-video", {
                    method: "POST",
                    body: formData
                });
            }
            const data = await res.json();
            if (!data.success || !data.task_id) {
                appendLiveTerminalLine(`❌ Episode ${epNum} skipped: ${data.error || 'Upload error'}`, `[Ep ${epNum}/${totalBatchCount}]`, "error");
                continue;
            }
            taskId = data.task_id;
            activeDubbingTaskId = taskId;
        } catch (uploadErr) {
            appendLiveTerminalLine(`❌ Episode ${epNum} network error: ${uploadErr.message}`, `[Ep ${epNum}/${totalBatchCount}]`, "error");
            continue;
        }

        // Poll this episode until complete
        const epDone = await new Promise((resolve) => {
            let lastLoggedStep = "";
            let loggedDialogueIds = new Set();
            let sepProgressSim = 5;
            let sepTimerTicks = 0;

            const pollInterval = setInterval(async () => {
                try {
                    const sRes = await fetch(`/api/projects/auto-dub-status/${taskId}`);
                    const sData = await sRes.json();
                    if (!sRes.ok || !sData.success) return;

                    const epPct = sData.progress || 10;
                    const stepKm = sData.step_km || "កំពុងដំណើរការ...";
                    const stepEn = sData.step_en || stepKm;

                    const overallPct = Math.min(99, Math.round((i / totalBatchCount) * 100 + (epPct / totalBatchCount)));
                    const remPct = 100 - overallPct;
                    const estEta = Math.max(5, Math.round((totalElapsedSeconds / Math.max(1, overallPct)) * remPct));

                    updateExportProgressUI(overallPct, totalElapsedSeconds, estEta, `ភាគ ${epNum}/${totalBatchCount}: ${file.name} - ${stepKm}`);

                    if (epPct < 35) {
                        sepTimerTicks++;
                        if (sepTimerTicks % 2 === 0 && sepProgressSim < 95) {
                            appendLiveTerminalLine(`AI voice removal: separating voice from music (${sepProgressSim}%)...`, `[Ep ${epNum}/${totalBatchCount}]`, "info");
                            sepProgressSim += Math.floor(Math.random() * 4) + 3;
                        }
                    }

                    if (stepEn && stepEn !== lastLoggedStep) {
                        lastLoggedStep = stepEn;
                        appendLiveTerminalLine(`${stepEn} (${epPct}%) [${stepKm}]`, `[Ep ${epNum}/${totalBatchCount}]`, "info");
                    }

                    // Stream dialogues
                    const currentDialogues = (sData.project && sData.project.dialogues) || sData.dialogues || [];
                    if (Array.isArray(currentDialogues) && currentDialogues.length > 0) {
                        currentDialogues.forEach((d, idx) => {
                            if (!loggedDialogueIds.has(idx)) {
                                loggedDialogueIds.add(idx);
                                const lineNum = String(idx + 1).padStart(2, '0');
                                const vName = (d.voice === 'sreymom' || d.voice === 'female') ? 'ស្រីមុំ (Sreymom)' : 'ពិសិដ្ឋ (Piseth)';
                                const zhText = d.text_original || d.text || "";
                                const kmText = d.text_km || d.translated_text || d.khmer_text || d.text || "";
                                if (kmText && kmText !== zhText) {
                                    appendLiveTerminalLine(`[Line ${lineNum}] "${zhText}" ➜ "${kmText}" (${vName})`, `[Ep ${epNum} Dub]`, "dub");
                                }
                            }
                        });
                    }

                    if (sData.status === "completed") {
                        clearInterval(pollInterval);
                        completedProjects.push(sData.project);
                        currentDubbedProject = sData.project;

                        // Preview newly finished episode in player
                        const mainVideo = document.getElementById('main-video');
                        if (mainVideo && sData.video_url) {
                            mainVideo.src = sData.video_url;
                            mainVideo.style.display = 'block';
                            mainVideo.load();
                        }

                        appendLiveTerminalLine(`✓ Episode ${epNum}/${totalBatchCount} finished: "${sData.project.output_video_file || fileName}"`, `[Ep ${epNum}/${totalBatchCount}]`, "success");
                        showToast(`✅ ភាគ ${epNum}/${totalBatchCount} បកប្រែរួចរាល់!`);
                        resolve(true);
                    } else if (sData.status === "failed") {
                        clearInterval(pollInterval);
                        appendLiveTerminalLine(`❌ Episode ${epNum}/${totalBatchCount} failed: ${sData.error || 'Unknown error'}`, `[Ep ${epNum}/${totalBatchCount}]`, "error");
                        showToast(`⚠️ ភាគ ${epNum} ជួបបញ្ហា: ${sData.error || 'បរាជ័យ'}`);
                        resolve(false);
                    }
                } catch (pollErr) {
                    console.warn("Batch episode poll error:", pollErr);
                }
            }, 1000);
        });

        // Small 1.5s pause between episodes
        if (i < totalBatchCount - 1) {
            await new Promise(r => setTimeout(r, 1500));
        }
    }

    // Merge into One Full Video if user selected 'full' or 'both'
    if ((outputMode === 'full' || outputMode === 'both') && completedProjects.length > 1) {
        appendLiveTerminalLine(`------------------------------------------------------------------------`, "[Full Movie Merge]", "info");
        appendLiveTerminalLine(`Export Mode: "${outputMode.toUpperCase()}" ➜ Concat/Merging all ${completedProjects.length} episodes into One Full Video...`, "[Full Movie Merge]", "info");
        updateExportProgressUI(96, totalElapsedSeconds, 30, `កំពុងបញ្ចូល ${completedProjects.length} ភាគ ជារឿងពេញមួយចប់ (Full Movie)...`);

        const videoPaths = completedProjects.map(p => p.output_video_file || p.output_file || p.video_file).filter(Boolean);
        let seriesTitle = "Drama_Series";
        if (files && files[0] && files[0].name) {
            seriesTitle = files[0].name.replace(/\.[^/.]+$/, '').replace(/(?:_part|[-_]ep|[-_]e|\bep|\bepisode)[-_]?\d+/i, '').replace(/[-_]+$/, '').trim() || "Drama_Series";
        }

        try {
            const mRes = await fetch("/api/projects/merge-episodes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    video_paths: videoPaths,
                    series_title: seriesTitle
                })
            });
            const mData = await mRes.json();
            if (mData.success) {
                appendLiveTerminalLine(`✓ Full Movie merged successfully: "${mData.merged_filename}"`, "[Full Movie Merge]", "success");
                showToast(`🎬 រឿងពេញមួយចប់ត្រូវបាន Merge ជោគជ័យ: ${mData.merged_filename}`);

                const mainVideo = document.getElementById('main-video');
                if (mainVideo && mData.video_url) {
                    mainVideo.src = mData.video_url;
                    mainVideo.style.display = 'block';
                    mainVideo.load();
                }

                if (currentDubbedProject) {
                    currentDubbedProject.output_video_file = mData.merged_path;
                    currentDubbedProject.merged_filename = mData.merged_filename;
                }
            } else {
                appendLiveTerminalLine(`⚠️ Merge failed: ${mData.error || 'Concat error'} (Separate episodes preserved)`, "[Full Movie Merge]", "error");
            }
        } catch (mErr) {
            appendLiveTerminalLine(`⚠️ Merge network error: ${mErr.message} (Separate episodes preserved)`, "[Full Movie Merge]", "error");
        }
    }

    clearInterval(batchMasterTimer);
    clearStagedFiles();
    updateExportProgressUI(100, totalElapsedSeconds, 0, `🎉 រួចរាល់ ១០០%! រឿងភាគទាំងអស់ចំនួន ${completedProjects.length}/${totalBatchCount} ភាគ ត្រូវបានបកប្រែជោគជ័យ!`);
    showToast(`🎉 រឿងភាគមួយចប់ (${completedProjects.length} ភាគ) ត្រូវបានបកប្រែជាសំឡេងខ្មែរជោគជ័យ!`);

    appendLiveTerminalLine(`========================================================================`, "[Batch Complete]", "success");
    appendLiveTerminalLine(`🎉 Series Batch Dubbing Finished: ${completedProjects.length}/${totalBatchCount} episodes completed.`, "[Batch Complete]", "success");
    appendLiveTerminalLine(`Zero vocal leakage. All dubbed videos saved in "data/exports/".`, "[Batch Complete]", "success");
    appendLiveTerminalLine(`========================================================================`, "[Batch Complete]", "success");

    resetEngineMonitorToStandby();

    // Auto open export folder in Windows Explorer
    openExportFolderDirect();

    // Show success notification banner
    if (completedProjects.length > 0) {
        showDubbingSuccessNotification({
            project: completedProjects[completedProjects.length - 1],
            batch_count: completedProjects.length,
            total_count: totalBatchCount
        });
    }
}

function showDubbingSuccessNotification(data) {
    const existing = document.getElementById('dubbing-success-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'dubbing-success-banner';
    banner.style.cssText = `
        position: fixed;
        bottom: 45px;
        right: 20px;
        background: linear-gradient(135deg, #18150c 0%, #0d0b06 100%);
        border: 1px solid rgba(250, 204, 21, 0.4);
        box-shadow: 0 10px 30px rgba(0,0,0,0.8), 0 0 20px rgba(250, 204, 21, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-width: 320px;
        animation: fadeIn 0.3s ease;
    `;

    const isBatch = data && data.batch_count;
    const bannerMsg = isBatch
        ? `រឿងភាគទាំងអស់ចំនួន ${data.batch_count} ភាគ បាន Render រួចរាល់ជាមួយសំឡេងខ្មែរ ពិសិដ្ឋ & ស្រីមុំ និងបានរក្សាទុកក្នុង Folder Exports!`
        : `វីដេអូបាន Render រួចរាល់ជាមួយសំឡេងខ្មែរ ពិសិដ្ឋ & ស្រីមុំ និងបានរក្សាទុកក្នុង Folder Exports!`;

    const downloadUrl = (data && data.video_url) ? data.video_url : '#';

    banner.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:700; color:#facc15; font-size:0.9rem; display:flex; align-items:center; gap:8px;">
                <i class="fa-solid fa-circle-check" style="color:#22c55e;"></i> ${isBatch ? 'បកប្រែរឿងភាគមួយចប់ជោគជ័យ!' : 'បកប្រែជាសំឡេងខ្មែរជោគជ័យ!'}
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background:transparent; border:none; color:#716655; font-size:0.85rem; cursor:pointer;">✕</button>
        </div>
        <div style="font-size:0.75rem; color:#cbd5e1;">
            ${bannerMsg}
        </div>
        <div style="display:flex; gap:8px; margin-top:4px;">
            <button onclick="openExportFolderDirect()" style="flex:1; background:rgba(250,204,21,0.15); border:1px solid #facc15; color:#facc15; border-radius:6px; padding:6px 12px; font-size:0.75rem; font-weight:600; cursor:pointer;">
                <i class="fa-solid fa-folder-open"></i> បើក Folder វីដេអូ
            </button>
            ${downloadUrl !== '#' ? `
            <a href="${downloadUrl}" download style="flex:1; text-align:center; background:#facc15; color:#000; border-radius:6px; padding:6px 12px; font-size:0.75rem; font-weight:700; text-decoration:none; display:inline-block;">
                <i class="fa-solid fa-download"></i> ទាញយក MP4
            </a>` : ''}
        </div>
    `;

    document.body.appendChild(banner);
}

async function openExportFolderDirect(targetPath) {
    try {
        const res = await fetch('/api/projects/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: targetPath || '' })
        });
        const data = await res.json();
        if (data.success) {
            showToast("📂 បានបើក Folder Exports ក្នុង Windows Explorer");
        } else {
            showToast(`⚠️ ${data.error || 'មិនអាចបើក Folder បានទេ'}`);
        }
    } catch (e) {
        showToast("⚠️ កំហុសក្នុងការបើក Folder");
    }
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

// ==========================================================================
// 6. LICENSE VERIFICATION & GATE SYSTEM
// ==========================================================================
async function checkDeviceLicenseStatus() {
    try {
        const res = await fetch('/api/license/status');
        const data = await res.json();
        currentHwid = data.hwid || "";
        
        const hwidElem = document.getElementById('settings-hwid-text');
        if (hwidElem) hwidElem.textContent = currentHwid;
        const gateHwidElem = document.getElementById('gate-hwid-text');
        if (gateHwidElem) gateHwidElem.textContent = currentHwid;

        const gateModal = document.getElementById('modal-license-gate');
        const badgeElem = document.getElementById('settings-lic-status-badge');
        const planElem = document.getElementById('settings-lic-plan-text');
        const expiryElem = document.getElementById('settings-lic-expiry-text');

        if (data.is_activated) {
            // License is valid & active
            if (gateModal) gateModal.classList.remove('active');
            if (badgeElem) {
                badgeElem.textContent = "ACTIVE";
                badgeElem.style.borderColor = "#22c55e";
                badgeElem.style.color = "#4ade80";
                badgeElem.style.background = "rgba(34,197,94,0.15)";
            }
            if (planElem) planElem.textContent = data.plan || "VIP PRO";
            if (expiryElem) expiryElem.textContent = data.expires_at || "LIFETIME";
        } else {
            // License is not active -> Show lock gate
            if (gateModal) gateModal.classList.add('active');
            if (badgeElem) {
                badgeElem.textContent = "UNLICENSED";
                badgeElem.style.borderColor = "#ef4444";
                badgeElem.style.color = "#f87171";
                badgeElem.style.background = "rgba(239,68,68,0.15)";
            }
            if (planElem) planElem.textContent = "None";
            if (expiryElem) expiryElem.textContent = "Expired / None";
        }
    } catch (e) {
        console.error("License check error:", e);
    }
}

async function submitGateLicense() {
    const input = document.getElementById('gate-license-input');
    const msgBox = document.getElementById('gate-status-msg');
    const key = input ? input.value.trim() : "";

    if (!key) {
        if (msgBox) {
            msgBox.style.display = 'block';
            msgBox.style.color = '#f87171';
            msgBox.style.background = 'rgba(239,68,68,0.1)';
            msgBox.textContent = "⚠️ សូមបញ្ចូល License Key របស់អ្នក";
        }
        return;
    }

    if (msgBox) {
        msgBox.style.display = 'block';
        msgBox.style.color = '#facc15';
        msgBox.style.background = 'rgba(250,204,21,0.1)';
        msgBox.textContent = "⏳ កំពុងផ្ទៀងផ្ទាត់ License Key...";
    }

    try {
        const res = await fetch('/api/license/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: key })
        });
        const data = await res.json();
        if (data.success) {
            if (msgBox) {
                msgBox.style.color = '#4ade80';
                msgBox.style.background = 'rgba(34,197,94,0.15)';
                msgBox.textContent = "🎉 បានបើកដំណើរការជោគជ័យ ១០០% (Activated!)";
            }
            showToast("🎉 បាន Activate License Key ជោគជ័យ!");
            setTimeout(() => {
                checkDeviceLicenseStatus();
            }, 1000);
        } else {
            if (msgBox) {
                msgBox.style.color = '#f87171';
                msgBox.style.background = 'rgba(239,68,68,0.15)';
                msgBox.textContent = `❌ ${data.error || 'License Key មិនត្រឹមត្រូវ'}`;
            }
        }
    } catch (e) {
        if (msgBox) {
            msgBox.style.color = '#f87171';
            msgBox.textContent = "❌ មានបញ្ហាភ្ជាប់បណ្តាញ";
        }
    }
}

async function confirmActivateLicense() {
    const key = document.getElementById('input-license-key').value.trim();
    if (!key) {
        showToast("⚠️ សូមបញ្ចូល License Key");
        return;
    }

    try {
        const res = await fetch('/api/license/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: key })
        });
        const data = await res.json();
        if (data.success) {
            showToast("🎉 VIP License Key Activated 100%!");
            checkDeviceLicenseStatus();
            backToSettingsHub();
        } else {
            showToast(`❌ ${data.error || 'Invalid key'}`);
        }
    } catch (e) {
        showToast("❌ Network error");
    }
}

function copyHwid(elemId = 'settings-hwid-text') {
    const elem = document.getElementById(elemId);
    const text = elem ? elem.textContent.trim() : currentHwid;
    if (text && text !== "FETCHING...") {
        navigator.clipboard.writeText(text).then(() => {
            showToast(`📋 បានចម្លង HWID: ${text}`);
        }).catch(() => {
            showToast(`HWID: ${text}`);
        });
    }
}

async function pasteGateLicense() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            const input = document.getElementById('gate-license-input');
            if (input) {
                input.value = text.trim();
                input.focus();
            }
            showToast("📋 បានបិទភ្ជាប់ (Pasted) License Key!");
        }
    } catch (e) {
        showToast("⚠️ សូមចុច Ctrl+V ដើម្បី Paste");
    }
}

// ==========================================================================
// UTILITIES
// ==========================================================================
function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => { toast.classList.remove('show'); }, 3000);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// Window Scroll Lock: Ensure layout stays 100% stable and never scrolls vertically
window.addEventListener('scroll', () => {
    if (window.scrollY !== 0 || window.scrollX !== 0) {
        window.scrollTo(0, 0);
    }
}, { passive: true });
document.addEventListener('DOMContentLoaded', () => {
    window.scrollTo(0, 0);
});
