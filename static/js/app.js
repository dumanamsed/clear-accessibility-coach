(function () {
    "use strict";

    var STRAND_DEFINITIONS = {
        C: { name: "Caption Everything", definition: "Video, audio, and embedded media must have accurate captions and transcripts.", link: "https://pressbooks.montgomerycollege.edu/clear/chapter/c-caption-everything/", color: "#0095C8" },
        L: { name: "Logical Layout", definition: "Use proper heading hierarchy, slide titles, semantic structure, and predictable navigation.", link: "https://pressbooks.montgomerycollege.edu/clear/chapter/l-logical-layout/", color: "#51237F" },
        E: { name: "Easy to Read", definition: "Use readable fonts and sizes, sufficient color contrast, plain language, short paragraphs, and chunked content.", link: "https://pressbooks.montgomerycollege.edu/clear/chapter/e-easy-to-read/", color: "#FBA93E" },
        A: { name: "Alt Text for Images", definition: "Provide meaningful image descriptions; mark decorative images as such.", link: "https://pressbooks.montgomerycollege.edu/clear/chapter/a-alt-text-for-images/", color: "#00AC9B" },
        R: { name: "Responsive Design", definition: "Content works across screen sizes, devices, and assistive technology.", link: "https://pressbooks.montgomerycollege.edu/clear/chapter/r-responsive-design/", color: "#B82A91" }
    };
    var STRAND_ORDER = ["C", "L", "E", "A", "R"];
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

    function submitAnalysis(formData) {
        showScreen("analyzing");
        startAnalyzingMessages();

        fetch("/analyze", { method: "POST", body: formData })
            .then(function (res) {
                if (!res.ok) return res.json().then(function (d) { throw new Error(d.error || "Analysis failed"); });
                return res.json();
            })
            .then(function (data) {
                reportData = data;
                renderReport(data);
                showScreen("report");
            })
            .catch(function (err) {
                showScreen("upload");
                showError(err.message);
            });
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
        var html = [];

        // Header
        html.push('<div class="report-header">');
        html.push('<h2 class="report-title">CLEAR Accessibility Report</h2>');
        html.push('<p class="report-filename">' + escapeHtml(data.filename) + '</p>');
        html.push('<p class="report-summary">' + data.total_findings + ' item' + (data.total_findings !== 1 ? 's' : '') + ' to review across ' + data.strands_with_findings + ' of 5 CLEAR strands.</p>');
        html.push('<p class="report-citation">' + FRAMEWORK_CITATION + '</p>');
        if (!data.claude_available) {
            html.push('<p class="report-claude-notice">AI-powered suggestions were not available for this analysis. Results are based on automated rule checks only.</p>');
        }
        html.push('</div>');

        // Strand dashboard (at-a-glance chips)
        html.push('<div class="strand-dashboard" role="group" aria-label="CLEAR strand summary">');
        STRAND_ORDER.forEach(function (key) {
            var strand = data.strands[key];
            var info = STRAND_DEFINITIONS[key];
            var isClear = strand.total === 0;
            var chipGold = (key === "E") ? " on-gold" : "";
            html.push('<button class="strand-chip' + (isClear ? ' clear' : '') + '" style="--chip-color:' + info.color + '" data-jump="' + key + '" aria-label="' + info.name + ': ' + strand.total + ' findings">');
            html.push('<span class="strand-chip-letter' + chipGold + '">' + key + '</span>');
            html.push('<div class="strand-chip-count">' + (isClear ? '✓' : strand.total) + '</div>');
            html.push('<div class="strand-chip-label">' + key + '</div>');
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

            html.push('<section class="strand-card' + (isOpen ? ' open' : '') + '" id="strand-' + key + '" style="--strand-color:' + info.color + '" aria-labelledby="strand-heading-' + key + '">');
            html.push('<button class="strand-header" id="strand-heading-' + key + '" aria-expanded="' + isOpen + '" aria-controls="strand-body-' + key + '" onclick="this.parentElement.classList.toggle(\'open\'); this.setAttribute(\'aria-expanded\', this.parentElement.classList.contains(\'open\'))">');
            html.push('<span class="strand-header-left">');
            html.push('<span class="strand-letter' + goldClass + '">' + key + '</span>');
            html.push('<span><span class="strand-name">' + info.name + '</span><br><span class="strand-count">' + (strand.total === 0 ? 'No issues found' : strand.total + ' item' + (strand.total !== 1 ? 's' : '') + ' to review') + '</span></span>');
            html.push('</span>');
            html.push('<svg class="strand-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>');
            html.push('</button>');

            html.push('<div class="strand-body" id="strand-body-' + key + '">');
            html.push('<p class="strand-definition">' + info.definition + '</p>');

            if (strand.total === 0) {
                html.push('<p class="no-findings-text">No issues detected for this strand. Nice work!</p>');
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
            responseEl.innerHTML = '<p>Consider adding captions to all remaining media. The CLEAR Framework recommends captioning everything — even short clips benefit from captions.</p><p style="margin-top: 8px;"><a href="https://pressbooks.montgomerycollege.edu/clear/chapter/c-caption-everything/" target="_blank" rel="noopener">Read the Caption Everything chapter in the CLEAR Pressbook</a> for step-by-step guidance on adding captions in common platforms.</p>';
        } else {
            responseEl.innerHTML = '<p>Captions are essential for accessibility. The CLEAR Framework’s Caption Everything strand recommends that all video and audio content include accurate, synchronized captions.</p><p style="margin-top: 8px;"><strong>Getting started:</strong></p><ul style="margin: 8px 0 0 20px; font-size: 0.9375rem; color: var(--text-secondary);"><li>YouTube and Panopto offer auto-captioning — always review for accuracy</li><li>Zoom and Teams can generate live captions and transcripts</li><li>For pre-recorded video, upload an SRT file or use your platform’s caption editor</li></ul><p style="margin-top: 8px;"><a href="https://pressbooks.montgomerycollege.edu/clear/chapter/c-caption-everything/" target="_blank" rel="noopener">Read the Caption Everything chapter in the CLEAR Pressbook</a></p>';
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
            return res.text();
        })
        .then(function (html) {
            var w = window.open("", "_blank");
            w.document.write(html);
            w.document.close();
            w.onload = function () { w.print(); };
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
