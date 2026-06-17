(function () {
    "use strict";

    // Definitions use each strand's official subtitle and signature line from
    // the published Pressbook. Links point to the strand intro pages at
    // /part/<slug>/ — the /chapter/ slugs resolve to quizzes or 404.
    // "color" = full-brightness MC brand accent, decorative non-text use only.
    // "ink" = darkened same-hue variant clearing WCAG AA 4.5:1 for text use.
    var STRAND_DEFINITIONS = {
        C: { name: "Caption Everything", definition: "Making multimedia accessible to every learner: accurate captions for all video, transcripts for audio-only content, and meaningful sound cues included.", link: "https://pressbooks.montgomerycollege.edu/clear/part/c-caption-everything/", color: "#0095C8", ink: "#006A94" },
        L: { name: "Logical Layout", definition: "Designing navigation that reduces confusion and cognitive load: predictable structure, headings in the correct order, and consistent organization. Clarity is an accessibility feature.", link: "https://pressbooks.montgomerycollege.edu/clear/part/l-logical-layout/", color: "#51237F", ink: "#51237F" },
        E: { name: "Easy to Read", definition: "Writing and formatting that supports comprehension: readable fonts, sufficient contrast, plain language, and short, digestible sections. Readability is access.", link: "https://pressbooks.montgomerycollege.edu/clear/part/e-easy-to-read/", color: "#FBA93E", ink: "#8A5A00" },
        A: { name: "Alt Text for Images", definition: "Ensuring visual information is not lost: meaningful descriptions for instructional images, with decorative images marked so screen readers can skip them. Alt text is a teaching choice.", link: "https://pressbooks.montgomerycollege.edu/clear/part/a-alt-text-for-images/", color: "#00AC9B", ink: "#0A7065" },
        R: { name: "Responsive Design", definition: "Designing for learning across devices: content that flows cleanly on phones and laptops alike, resizes properly, and avoids images of text. Device access is equity access.", link: "https://pressbooks.montgomerycollege.edu/clear/part/r-responsive-design/", color: "#B82A91", ink: "#B82A91" }
    };
    var STRAND_ORDER = ["C", "L", "E", "A", "R"];

    // CLEAR self-assessment items an automated tool can't verify from a file —
    // shown per strand so the full requirement set stays visible.
    var MANUAL_CHECKS = {
        C: ["Captions are accurate and edited for clarity, spelling, and timing — not just auto-generated.", "Audio-only content (podcasts, narration) has a transcript.", "Meaningful non-speech audio (music, sound effects) is described, and speakers are identified.", "Live sessions include captions when possible."],
        L: ["Reading and focus order follow a logical, intuitive path.", "Everything is operable by keyboard alone, and the keyboard focus indicator is visible.", "Interactive elements meet the 24×24 px minimum target size.", "Any drag-based interaction has a non-drag alternative."],
        E: ["Text can be resized to 200% without losing content or breaking layout.", "Information is never conveyed by color alone (also use text, icons, or labels).", "A dark-mode or high-contrast option is offered where the platform supports it."],
        A: ["Each description conveys the image's purpose and meaning, not just its appearance.", "Charts, graphs, and infographics have a text summary or extended description of the data.", "Purely decorative images are intentionally marked decorative so screen readers skip them."],
        R: ["Tested on multiple devices — desktop, tablet, and phone.", "Content reflows with no horizontal scrolling on small screens.", "Links and buttons are easy to see and tap on touch screens.", "Shared in accessible formats (structured Word, tagged PDF)."]
    };
    var FRAMEWORK_CITATION = "Grounded in the CLEAR Framework by Dr. Paul D. Miller, Ed.D., Montgomery College Center for Teaching and Learning.";

    var ANALYZING_MESSAGES = [
        "Checking captions...",
        "Reviewing layout and structure...",
        "Evaluating readability...",
        "Reading alt text...",
        "Checking responsive design...",
        "Running AI-powered review...",
        "Generating your coaching report..."
    ];

    var reportData = null;

    // Tab switching
    var tabs = document.querySelectorAll(".tab");
    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            tabs.forEach(function (t) {
                t.classList.remove("active");
                t.setAttribute("aria-selected", "false");
            });
            tab.classList.add("active");
            tab.setAttribute("aria-selected", "true");

            document.querySelectorAll(".tab-panel").forEach(function (p) {
                p.hidden = true;
            });
            var panelId = tab.getAttribute("aria-controls");
            document.getElementById(panelId).hidden = false;
        });

        tab.addEventListener("keydown", function (e) {
            var idx = Array.from(tabs).indexOf(tab);
            if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                var next = e.key === "ArrowRight" ? (idx + 1) % tabs.length : (idx - 1 + tabs.length) % tabs.length;
                tabs[next].click();
                tabs[next].focus();
            }
        });
    });

    // Drop zone
    var dropZone = document.getElementById("drop-zone");
    var fileInput = document.getElementById("file-input");
    var fileSelected = document.getElementById("file-selected");
    var btnAnalyzeFile = document.getElementById("btn-analyze-file");

    if (dropZone) {
        dropZone.addEventListener("click", function () { fileInput.click(); });
        dropZone.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
        });
        dropZone.addEventListener("dragover", function (e) { e.preventDefault(); dropZone.classList.add("drag-over"); });
        dropZone.addEventListener("dragleave", function () { dropZone.classList.remove("drag-over"); });
        dropZone.addEventListener("drop", function (e) {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                onFileSelected();
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", onFileSelected);
    }

    function onFileSelected() {
        if (fileInput.files.length) {
            var file = fileInput.files[0];
            fileSelected.textContent = "Selected: " + file.name + " (" + formatSize(file.size) + ")";
            btnAnalyzeFile.disabled = false;
        }
    }

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    // Paste area
    var pasteArea = document.getElementById("paste-area");
    var btnAnalyzePaste = document.getElementById("btn-analyze-paste");

    if (pasteArea) {
        pasteArea.addEventListener("input", function () {
            btnAnalyzePaste.disabled = !pasteArea.value.trim();
        });
    }

    // Upload form
    var uploadForm = document.getElementById("upload-form");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (e) {
            e.preventDefault();
            var formData = new FormData();
            formData.append("file", fileInput.files[0]);
            submitAnalysis(formData);
        });
    }

    // Paste form
    var pasteForm = document.getElementById("paste-form");
    if (pasteForm) {
        pasteForm.addEventListener("submit", function (e) {
            e.preventDefault();
            var formData = new FormData();
            formData.append("paste_content", pasteArea.value);
            var pasteType = document.querySelector('input[name="paste_type"]:checked').value;
            formData.append("paste_type", pasteType);
            submitAnalysis(formData);
        });
    }

    // AI pass state: 'disabled' (no API key), 'pending', 'done', 'unavailable'
    var aiState = "disabled";
    var mediaSelection = null;

    // The rule pass returns in milliseconds. Hold the analyzing screen for a
    // moment anyway: without it the report appears to "pop in" instantly with
    // preliminary numbers, which users read as an (often wrong) final verdict.
    var MIN_ANALYZING_MS = 1800;

    function submitAnalysis(formData) {
        showScreen("analyzing");
        startAnalyzingMessages();
        mediaSelection = null;
        var startedAt = Date.now();

        fetch("/analyze", { method: "POST", body: formData })
            .then(function (res) {
                if (!res.ok) return res.json().then(function (d) { throw new Error(d.error || "Analysis failed"); });
                return res.json();
            })
            .then(function (data) {
                reportData = data;
                aiState = data.claude_enabled ? "pending" : "disabled";
                var remaining = Math.max(0, MIN_ANALYZING_MS - (Date.now() - startedAt));
                setTimeout(function () {
                    renderReport(data);
                    showScreen("report");
                    if (aiState === "pending") startAiReview(data);
                }, remaining);
            })
            .catch(function (err) {
                showScreen("upload");
                showError(err.message);
            });
    }

    function startAiReview(data) {
        var ruleFindings = [];
        STRAND_ORDER.forEach(function (key) {
            data.strands[key].findings.forEach(function (f) { ruleFindings.push(f); });
        });

        fetch("/ai-review", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ai_context: data.ai_context, rule_findings: ruleFindings })
        })
            .then(function (res) {
                if (!res.ok) throw new Error("AI review failed");
                return res.json();
            })
            .then(function (result) {
                var announcement;
                if (result.claude_available && result.findings.length) {
                    mergeAiFindings(result.findings);
                    aiState = "done";
                    announcement = "Review complete. " + result.findings.length + " AI coaching suggestion" + (result.findings.length !== 1 ? "s" : "") + " added to the report.";
                } else {
                    aiState = result.claude_available ? "done" : "unavailable";
                    announcement = result.claude_available
                        ? "Review complete. No additional AI suggestions."
                        : "Review complete. AI suggestions were not available; the report shows automated rule checks only.";
                }
                rerenderPreservingContext(announcement);
            })
            .catch(function () {
                aiState = "unavailable";
                rerenderPreservingContext("AI suggestions were not available. The report shows automated rule checks only.");
            });
    }

    function rerenderPreservingContext(announcement) {
        // Re-rendering replaces the report DOM; keep the user's place:
        // remember the focused element's id and restore it afterwards, and
        // announce what changed via the persistent live region.
        var focusedId = document.activeElement ? document.activeElement.id : "";
        renderReport(reportData);
        restoreMediaSelection();
        if (focusedId) {
            var el = document.getElementById(focusedId);
            if (el) el.focus();
        }
        announce(announcement);
    }

    function announce(msg) {
        var region = document.getElementById("sr-announcer");
        if (!region) return;
        region.textContent = "";
        // Brief delay so repeat announcements with identical text still fire.
        setTimeout(function () { region.textContent = msg; }, 80);
    }

    function mergeAiFindings(findings) {
        findings.forEach(function (f) {
            var strand = reportData.strands[f.strand];
            if (!strand) return;
            strand.findings.push(f);
            strand.total += 1;
            if (f.severity === "critical") strand.critical += 1;
            else if (f.severity === "warning") strand.warning += 1;
            else strand.tip += 1;
        });
        var total = 0, withFindings = 0;
        STRAND_ORDER.forEach(function (key) {
            total += reportData.strands[key].total;
            if (reportData.strands[key].total > 0) withFindings += 1;
        });
        reportData.total_findings = total;
        reportData.strands_with_findings = withFindings;
        var cCount = reportData.strands.C.total;
        if (cCount > 0) {
            reportData.has_media = true;
            reportData.media_count = Math.max(reportData.media_count, cCount);
        }
    }

    function restoreMediaSelection() {
        if (!mediaSelection) return;
        var btn = document.querySelector('.media-btn[data-value="' + mediaSelection + '"]');
        if (btn) btn.click();
    }

    function showScreen(screen) {
        var uploadCard = document.querySelector(".upload-card");
        var introSection = document.querySelector(".intro-section");
        var analyzingScreen = document.getElementById("analyzing-screen");
        var reportScreen = document.getElementById("report-screen");

        uploadCard.hidden = screen !== "upload";
        introSection.hidden = screen !== "upload";
        analyzingScreen.hidden = screen !== "analyzing";
        reportScreen.hidden = screen !== "report";
    }

    var messageInterval = null;
    function startAnalyzingMessages() {
        var msgEl = document.getElementById("analyzing-message");
        var idx = 0;
        msgEl.textContent = ANALYZING_MESSAGES[0];
        messageInterval = setInterval(function () {
            idx = (idx + 1) % ANALYZING_MESSAGES.length;
            msgEl.textContent = ANALYZING_MESSAGES[idx];
        }, 2200);
    }

    function showError(msg) {
        var existing = document.querySelector(".error-notice");
        if (existing) existing.remove();
        var div = document.createElement("div");
        div.className = "error-notice";
        div.setAttribute("role", "alert");
        div.textContent = msg;
        document.querySelector(".upload-card").before(div);
        setTimeout(function () { div.remove(); }, 8000);
    }

    function renderReport(data) {
        if (messageInterval) { clearInterval(messageInterval); messageInterval = null; }
        var container = document.getElementById("report-screen");
        var pending = aiState === "pending";
        // Class on the container drives the "dim the preliminary results" CSS.
        container.className = pending ? "is-pending" : "";
        var html = [];

        // Unmissable in-progress banner: sticks to the top of the report and
        // visually dominates so a still-loading report can never be mistaken
        // for a finished "no issues" verdict.
        if (pending) {
            html.push('<div class="progress-banner" role="status" aria-live="assertive">');
            html.push('<div class="progress-banner-row">');
            html.push('<span class="progress-spinner" aria-hidden="true"></span>');
            html.push('<div><div class="progress-banner-title">Review still in progress — not final yet</div>');
            html.push('<div class="progress-banner-sub">The AI coaching review is still scanning your file. Please wait for the “Review complete” message before assuming your file is clear.</div></div>');
            html.push('</div>');
            html.push('<div class="progress-bar" aria-hidden="true"><span></span></div>');
            html.push('</div>');
        }

        // Header
        html.push('<div class="report-header">');
        html.push('<h2 class="report-title">CLEAR Accessibility Report</h2>');
        html.push('<p class="report-filename">' + escapeHtml(data.filename) + '</p>');
        // While the AI pass is running, the numbers are preliminary — phrase
        // them that way so an early "0 items" doesn't read as a final verdict.
        var summaryText;
        if (pending) {
            summaryText = data.total_findings === 0
                ? "Preliminary checks passed — still reviewing…"
                : data.total_findings + " item" + (data.total_findings !== 1 ? "s" : "") + " found so far — still reviewing…";
        } else if (data.total_findings === 0) {
            summaryText = "Review complete: no issues found across all 5 CLEAR strands. Nice work!";
        } else {
            summaryText = "Review complete: " + data.total_findings + " item" + (data.total_findings !== 1 ? "s" : "") + " to review across " + data.strands_with_findings + " of 5 CLEAR strands.";
        }
        html.push('<p class="report-summary">' + summaryText + '</p>');
        html.push('<p class="report-citation">' + FRAMEWORK_CITATION + '</p>');
        if (!pending && (aiState === "unavailable" || aiState === "disabled")) {
            html.push('<p class="report-claude-notice">AI-powered suggestions were not available for this analysis. Results are based on automated rule checks only.</p>');
        }
        html.push('</div>');

        // Strand dashboard (at-a-glance chips)
        html.push('<div class="strand-dashboard" role="group" aria-label="CLEAR strand summary">');
        STRAND_ORDER.forEach(function (key) {
            var strand = data.strands[key];
            var info = STRAND_DEFINITIONS[key];
            var isClear = strand.total === 0;
            var pending = aiState === "pending";
            var chipGold = (key === "E") ? " on-gold" : "";
            // No checkmark until the AI verdict is in — "…" signals the strand
            // is still under review rather than confirmed clean.
            var countDisplay = isClear ? (pending ? "…" : "✓") : strand.total;
            var countLabel = isClear
                ? (pending ? "review in progress" : "no issues found")
                : strand.total + " item" + (strand.total !== 1 ? "s" : "") + " to review";
            html.push('<button class="strand-chip' + (isClear && !pending ? ' clear' : '') + '" style="--chip-color:' + info.color + ';--strand-ink:' + info.ink + '" data-jump="' + key + '" aria-label="' + info.name + ': ' + countLabel + '">');
            html.push('<span class="strand-chip-letter' + chipGold + '" aria-hidden="true">' + key + '</span>');
            html.push('<div class="strand-chip-count" aria-hidden="true">' + countDisplay + '</div>');
            html.push('<div class="strand-chip-label" aria-hidden="true">' + key + '</div>');
            html.push('</button>');
        });
        html.push('</div>');

        // Media follow-up panel
        if (data.has_media) {
            html.push(renderMediaPanel(data.media_count));
        }

        // Strand sections
        STRAND_ORDER.forEach(function (key) {
            var strand = data.strands[key];
            var info = STRAND_DEFINITIONS[key];
            var isOpen = strand.total > 0;
            var goldClass = (key === "E") ? " on-gold" : "";

            html.push('<section class="strand-card' + (isOpen ? ' open' : '') + '" id="strand-' + key + '" style="--strand-color:' + info.color + ';--strand-ink:' + info.ink + '" aria-labelledby="strand-heading-' + key + '">');
            // The button is wrapped in an <h3> so screen reader users can jump
            // between strands with heading navigation.
            html.push('<h3 class="strand-h">');
            html.push('<button class="strand-header" id="strand-heading-' + key + '" aria-expanded="' + isOpen + '" aria-controls="strand-body-' + key + '" onclick="this.closest(\'.strand-card\').classList.toggle(\'open\'); this.setAttribute(\'aria-expanded\', this.closest(\'.strand-card\').classList.contains(\'open\'))">');
            html.push('<span class="strand-header-left">');
            html.push('<span class="strand-letter' + goldClass + '" aria-hidden="true">' + key + '</span>');
            var subText = strand.total === 0
                ? (aiState === "pending" ? "No issues so far" : "No issues found")
                : strand.total + " item" + (strand.total !== 1 ? "s" : "") + " to review";
            html.push('<span><span class="strand-name">' + info.name + '</span><br><span class="strand-count">' + subText + '</span></span>');
            html.push('</span>');
            html.push('<svg class="strand-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>');
            html.push('</button>');
            html.push('</h3>');

            html.push('<div class="strand-body" id="strand-body-' + key + '">');
            html.push('<p class="strand-definition">' + info.definition + '</p>');

            if (strand.total === 0) {
                html.push('<p class="no-findings-text">' + (aiState === "pending"
                    ? "No rule-based issues detected. The AI coaching review may add suggestions shortly."
                    : "No issues detected for this strand. Nice work!") + '</p>');
            } else {
                html.push('<div class="strand-badges">');
                if (strand.critical) html.push('<span class="badge badge-critical">' + strand.critical + ' critical</span>');
                if (strand.warning) html.push('<span class="badge badge-warning">' + strand.warning + ' warning' + (strand.warning !== 1 ? 's' : '') + '</span>');
                if (strand.tip) html.push('<span class="badge badge-tip">' + strand.tip + ' tip' + (strand.tip !== 1 ? 's' : '') + '</span>');
                html.push('</div>');

                strand.findings.forEach(function (f) {
                    html.push('<article class="finding-item severity-' + f.severity + '">');
                    html.push('<div class="finding-meta">');
                    html.push('<span class="badge badge-' + f.severity + '">' + f.severity + '</span>');
                    html.push('<span class="finding-location">' + escapeHtml(f.location) + '</span>');
                    if (f.source === "claude") html.push('<span class="finding-source-tag">AI coaching</span>');
                    html.push('</div>');
                    html.push('<p class="finding-issue">' + escapeHtml(f.issue) + '</p>');
                    if (f.evidence) html.push('<p class="finding-evidence">' + escapeHtml(f.evidence) + '</p>');
                    if (f.suggestion) html.push('<div class="finding-suggestion">' + escapeHtml(f.suggestion) + '</div>');
                    html.push('</article>');
                });
            }

            // Manual CLEAR checklist — requirements the tool can't auto-verify.
            var checks = MANUAL_CHECKS[key] || [];
            if (checks.length) {
                html.push('<details class="manual-checks"><summary>Also verify yourself (CLEAR checklist the tool can’t auto-check)</summary><ul>');
                checks.forEach(function (c) { html.push('<li>' + escapeHtml(c) + '</li>'); });
                html.push('</ul></details>');
            }
            html.push('<p class="strand-learn-more"><a href="' + info.link + '" target="_blank" rel="noopener">Learn more about ' + info.name + ' in the CLEAR Pressbook</a></p>');
            html.push('</div>');
            html.push('</section>');
        });

        // Encouragement
        html.push('<div class="encouragement-card">');
        html.push('<p>Making your materials accessible is a journey, not a destination. Every improvement you make helps your students engage more fully with your content. The items above are starting points — tackle the critical ones first, then work through warnings and tips at your own pace.</p>');
        html.push('<p>For detailed guidance, explore the <a href="https://pressbooks.montgomerycollege.edu/clear/" target="_blank" rel="noopener">CLEAR Pressbook</a> or reach out to the <a href="mailto:' + CTL_EMAIL + '">Center for Teaching and Learning</a> for one-on-one support.</p>');
        html.push('<p class="encouragement-source">Source: CLEAR Framework, Dr. Paul D. Miller, Montgomery College CTL.</p>');
        html.push('</div>');

        // Actions
        html.push('<div class="report-actions">');
        html.push('<button class="btn btn-primary" id="btn-download-pdf">Download report (PDF)</button>');
        html.push('<button class="btn btn-secondary" id="btn-start-over">Start over</button>');
        html.push('</div>');

        container.innerHTML = html.join("");

        // Bind actions
        document.getElementById("btn-download-pdf").addEventListener("click", downloadPdf);
        document.getElementById("btn-start-over").addEventListener("click", function () {
            reportData = null;
            aiState = "disabled";
            mediaSelection = null;
            container.innerHTML = "";
            if (fileInput) { fileInput.value = ""; fileSelected.textContent = ""; btnAnalyzeFile.disabled = true; }
            if (pasteArea) { pasteArea.value = ""; btnAnalyzePaste.disabled = true; }
            showScreen("upload");
        });

        // Bind dashboard chip jump-to-strand
        container.querySelectorAll(".strand-chip").forEach(function (chip) {
            chip.addEventListener("click", function () {
                var key = chip.dataset.jump;
                var card = document.getElementById("strand-" + key);
                if (card) {
                    if (!card.classList.contains("open")) {
                        var hdr = card.querySelector(".strand-header");
                        card.classList.add("open");
                        if (hdr) hdr.setAttribute("aria-expanded", "true");
                    }
                    card.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            });
        });

        // Bind media buttons
        var mediaButtons = container.querySelectorAll(".media-btn");
        mediaButtons.forEach(function (btn) {
            btn.addEventListener("click", function () {
                mediaButtons.forEach(function (b) { b.classList.remove("selected"); });
                btn.classList.add("selected");
                mediaSelection = btn.dataset.value;
                handleMediaResponse(btn.dataset.value, data);
            });
        });
    }

    function renderMediaPanel(count) {
        var h = [];
        h.push('<div class="media-panel" role="region" aria-labelledby="media-heading">');
        h.push('<h3 id="media-heading">Video/Audio Captions</h3>');
        h.push('<p>We detected ' + count + ' video or audio element' + (count !== 1 ? 's' : '') + ' in your file. Are they captioned?</p>');
        h.push('<div class="media-buttons" role="group" aria-label="Caption status">');
        h.push('<button class="media-btn" data-value="yes">Yes, all captioned</button>');
        h.push('<button class="media-btn" data-value="some">Some captioned</button>');
        h.push('<button class="media-btn" data-value="no">No / not sure</button>');
        h.push('</div>');
        h.push('<div class="media-response" id="media-response" role="status"></div>');
        h.push('</div>');
        return h.join("");
    }

    function handleMediaResponse(value) {
        var responseEl = document.getElementById("media-response");
        responseEl.classList.add("visible");

        if (value === "yes") {
            responseEl.innerHTML = '<p style="color: var(--tip); font-weight: 500;">Great work! Captions make your content accessible to a wider audience, including students who are deaf or hard of hearing, non-native speakers, and learners in noisy or quiet environments.</p>';
        } else if (value === "some") {
            responseEl.innerHTML = '<p>Consider adding captions to all remaining media. The CLEAR Framework recommends captioning everything — even short clips benefit from captions.</p><p style="margin-top: 8px;"><a href="https://pressbooks.montgomerycollege.edu/clear/part/c-caption-everything/" target="_blank" rel="noopener">Read the Caption Everything strand in the CLEAR Pressbook</a> for step-by-step guidance on adding captions in common platforms.</p>';
        } else {
            responseEl.innerHTML = '<p>Captions are essential for accessibility. The CLEAR Framework’s Caption Everything strand recommends accurate captions for all video, transcripts for audio-only content, and review of auto-generated captions for accuracy.</p><p style="margin-top: 8px;"><strong>Step-by-step guides from the CLEAR Pressbook:</strong></p><ul style="margin: 8px 0 0 20px; font-size: 0.9375rem; color: var(--text-secondary);"><li><a href="https://pressbooks.montgomerycollege.edu/clear/chapter/how-to-add-captions-to-youtube-videos/" target="_blank" rel="noopener">How to add captions to YouTube videos</a></li><li><a href="https://pressbooks.montgomerycollege.edu/clear/chapter/turning-on-auto-captions-in-teams-or-zoom-for-live-presentations/" target="_blank" rel="noopener">Turning on auto-captions in Teams or Zoom</a></li><li><a href="https://pressbooks.montgomerycollege.edu/clear/chapter/tips-for-high-quality-captions/" target="_blank" rel="noopener">Tips for high-quality captions</a></li></ul><p style="margin-top: 8px;"><a href="https://pressbooks.montgomerycollege.edu/clear/part/c-caption-everything/" target="_blank" rel="noopener">Read the full Caption Everything strand</a></p>';
        }
    }

    function downloadPdf() {
        if (!reportData) return;
        var btn = document.getElementById("btn-download-pdf");
        btn.disabled = true;
        btn.textContent = "Generating PDF...";

        fetch("/export-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(reportData)
        })
        .then(function (res) {
            if (!res.ok) throw new Error("PDF generation failed");
            var type = res.headers.get("Content-Type") || "";
            if (type.indexOf("application/pdf") !== -1) {
                // Server rendered a real PDF — download it directly.
                return res.blob().then(function (blob) {
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement("a");
                    a.href = url;
                    a.download = "clear-accessibility-report.pdf";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(url);
                });
            }
            // Fallback: print-styled HTML — open it and trigger the print dialog.
            return res.text().then(function (html) {
                var w = window.open("", "_blank");
                w.document.write(html);
                w.document.close();
                w.onload = function () { w.print(); };
            });
        })
        .catch(function (err) {
            alert("Could not generate PDF: " + err.message);
        })
        .finally(function () {
            btn.disabled = false;
            btn.textContent = "Download report (PDF)";
        });
    }

    function escapeHtml(str) {
        if (!str) return "";
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // Expose CTL email for the report template
    var CTL_EMAIL = document.querySelector('meta[name="ctl-email"]');
    CTL_EMAIL = CTL_EMAIL ? CTL_EMAIL.content : "CTL@montgomerycollege.edu";

})();
