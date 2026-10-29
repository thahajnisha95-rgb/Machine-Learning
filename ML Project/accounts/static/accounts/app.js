(function () {
    var root = document.documentElement;
    var body = document.body;
    var sidebar = document.getElementById("app-sidebar");
    var backdrop = document.getElementById("sidebar-backdrop");
    var collapseBtn = document.getElementById("sidebar-collapse");
    var openBtn = document.getElementById("sidebar-open");
    var closeBtn = document.getElementById("sidebar-close");
    var themeBtn = document.getElementById("theme-toggle");
    var search = document.getElementById("global-search");
    var content = document.getElementById("app-content");
    var helpBtn = document.getElementById("help-toggle");
    var helpPanel = document.getElementById("help-panel");
    var menu = document.getElementById("account-menu");
    var tooltip = document.getElementById("nav-tooltip");
    var crumb = document.getElementById("crumb-current");
    var pageTitle = document.getElementById("page-title");
    var labels = {
        overview: "Dashboard",
        "my-learning": "My Learning",
        "skill-recommendations": "Skill Recommendations",
        "learning-resources": "Learning Resources",
        "learning-progress": "Learning Progress",
        profile: "My Profile"
    };

    var views = ["overview", "my-learning", "skill-recommendations", "learning-resources", "learning-progress"];

    function isMobile() {
        return window.matchMedia("(max-width: 767px)").matches;
    }

    function store(key, value) {
        try { localStorage.setItem(key, value); } catch (err) { /* private mode */ }
    }

    function read(key) {
        try { return localStorage.getItem(key); } catch (err) { return null; }
    }

    function setCollapsed(collapsed) {
        root.classList.toggle("sidebar-collapsed", collapsed);
        if (collapseBtn) {
            collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
            collapseBtn.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
            collapseBtn.setAttribute("data-tooltip", collapsed ? "Expand sidebar" : "Collapse sidebar");
        }
    }

    function setDrawer(open) {
        if (!sidebar) return;
        var wasOpen = sidebar.classList.contains("is-open");
        sidebar.classList.toggle("is-open", open);
        if (backdrop) backdrop.hidden = !open;
        if (openBtn) openBtn.setAttribute("aria-expanded", open ? "true" : "false");
        if (open && closeBtn) closeBtn.focus();
        if (!open && wasOpen && openBtn && isMobile()) openBtn.focus();
    }

    function setActive(key) {
        var links = document.querySelectorAll("[data-nav]");
        Array.prototype.forEach.call(links, function (link) {
            var on = link.getAttribute("data-nav") === key;
            link.classList.toggle("is-active", on);
            if (on) link.setAttribute("aria-current", "page");
            else link.removeAttribute("aria-current");
        });
        if (labels[key]) {
            if (crumb) crumb.textContent = labels[key];
            if (pageTitle) pageTitle.textContent = labels[key];
        }
    }

    function showView(key, opts) {
        opts = opts || {};
        if (views.indexOf(key) === -1) return;
        var changed = root.getAttribute("data-view") !== key;
        root.setAttribute("data-view", key);
        setActive(key);
        if (changed && content) content.scrollTop = 0;
        if (opts.hash && window.location.hash !== "#" + key) {
            if (window.history && window.history.replaceState) {
                window.history.replaceState(null, "", "#" + key);
            } else {
                window.location.hash = key;
            }
        }
        if (opts.focus) {
            var panel = document.getElementById(key);
            var heading = panel && panel.querySelector("h1, h2");
            if (heading) {
                if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
                heading.focus();
            }
        }
        if (opts.closeDrawer && isMobile()) setDrawer(false);
    }

    var courseInput = document.getElementById("id_course");
    var yearSelect = document.getElementById("id_year_of_study");
    if (courseInput && yearSelect) {
        var durationRules = JSON.parse(yearSelect.getAttribute("data-course-durations") || "{}");
        var coursePrefixes = Object.keys(durationRules).sort(function (a, b) {
            return b.length - a.length;
        });

        function updateStudyYears() {
            var course = courseInput.value.toLowerCase().replace(/[^a-z0-9]/g, "");
            var duration = 4;
            for (var i = 0; i < coursePrefixes.length; i += 1) {
                if (course.indexOf(coursePrefixes[i]) === 0) {
                    duration = durationRules[coursePrefixes[i]];
                    break;
                }
            }
            if (duration === 4 && /^(m|pg|postgraduate)/.test(course)) duration = 2;

            var labels = duration === 3
                ? ["First Year", "Second Year", "Final Year"]
                : duration === 2
                    ? ["First Year", "Final Year"]
                    : ["First Year", "Second Year", "Third Year", "Final Year"];
            var currentYear = yearSelect.value;
            yearSelect.textContent = "";
            labels.forEach(function (label, index) {
                var option = document.createElement("option");
                option.value = String(index + 1);
                option.textContent = label;
                yearSelect.appendChild(option);
            });
            yearSelect.value = Number(currentYear) <= labels.length ? currentYear : String(labels.length);
        }

        courseInput.addEventListener("input", updateStudyYears);
        updateStudyYears();
    }

    function hideTooltip() {
        if (tooltip) tooltip.hidden = true;
    }

    function showTooltip(el) {
        if (!tooltip || !el || isMobile() || !root.classList.contains("sidebar-collapsed")) {
            hideTooltip();
            return;
        }
        var label = el.getAttribute("data-tooltip");
        if (!label) {
            hideTooltip();
            return;
        }
        var rect = el.getBoundingClientRect();
        tooltip.textContent = label;
        tooltip.hidden = false;
        tooltip.style.top = (rect.top + rect.height / 2) + "px";
        tooltip.style.left = (rect.right + 10) + "px";
    }

    function closeHelp() {
        if (!helpPanel || helpPanel.hidden) return;
        helpPanel.hidden = true;
        if (helpBtn) helpBtn.setAttribute("aria-expanded", "false");
    }

    setCollapsed(read("learnpath-sidebar") === "collapsed");

    function syncTheme() {
        var dark = root.getAttribute("data-theme") === "dark";
        if (!themeBtn) return;
        themeBtn.setAttribute("aria-pressed", dark ? "true" : "false");
        themeBtn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    }
    syncTheme();

    if (themeBtn) {
        themeBtn.addEventListener("click", function () {
            var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            root.setAttribute("data-theme", next);
            store("learnpath-theme", next);
            syncTheme();
        });
    }

    if (collapseBtn) {
        collapseBtn.addEventListener("click", function () {
            var collapsed = !root.classList.contains("sidebar-collapsed");
            setCollapsed(collapsed);
            store("learnpath-sidebar", collapsed ? "collapsed" : "expanded");
            hideTooltip();
        });
    }

    if (openBtn) openBtn.addEventListener("click", function () { setDrawer(true); });
    if (closeBtn) closeBtn.addEventListener("click", function () { setDrawer(false); });
    if (backdrop) backdrop.addEventListener("click", function () { setDrawer(false); });

    window.addEventListener("resize", function () {
        if (!isMobile()) setDrawer(false);
        hideTooltip();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            setDrawer(false);
            closeHelp();
            if (menu && menu.open) menu.open = false;
            hideTooltip();
        }
        var tag = event.target && event.target.tagName;
        var typing = tag && /input|textarea|select/i.test(tag);
        if (event.key === "/" && !typing && search) {
            event.preventDefault();
            search.focus();
            if (typeof search.select === "function") search.select();
        }
    });

    function setSkillCard(card, open) {
        if (!card) return;
        var toggle = card.querySelector(".skill-toggle");
        var panelId = toggle && toggle.getAttribute("aria-controls");
        var panel = panelId && document.getElementById(panelId);
        if (!toggle || !panel) return;
        panel.hidden = !open;
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        var name = card.querySelector(".skill-name");
        var label = name ? name.textContent : "this skill";
        toggle.setAttribute("aria-label", (open ? "Hide courses for " : "Show courses for ") + label);
        card.classList.toggle("is-open", open);
    }

    document.addEventListener("click", function (event) {
        var skillToggle = event.target.closest ? event.target.closest(".skill-toggle") : null;
        if (skillToggle) {
            var card = skillToggle.closest(".skill-card");
            var willOpen = skillToggle.getAttribute("aria-expanded") !== "true";
            document.querySelectorAll(".skill-card.is-open").forEach(function (openCard) {
                if (openCard !== card) setSkillCard(openCard, false);
            });
            setSkillCard(card, willOpen);
        }
        var link = event.target.closest ? event.target.closest("a[href*='#']") : null;
        if (link && content) {
            var hash = link.hash || "";
            var id = hash.slice(1);
            var target = id && document.getElementById(id);
            if (target && content.contains(target) && views.indexOf(id) !== -1 && link.pathname === window.location.pathname) {
                event.preventDefault();
                showView(id, { hash: true, focus: true, closeDrawer: true });
            }
        }
        if (menu && menu.open && !menu.contains(event.target)) menu.open = false;
        if (helpPanel && !helpPanel.hidden && helpBtn && !helpBtn.contains(event.target) && !helpPanel.contains(event.target)) {
            closeHelp();
        }
    });

    if (helpBtn && helpPanel) {
        helpBtn.addEventListener("click", function () {
            var willOpen = helpPanel.hidden;
            helpPanel.hidden = !willOpen;
            helpBtn.setAttribute("aria-expanded", willOpen ? "true" : "false");
        });
    }

    Array.prototype.forEach.call(document.querySelectorAll("[data-tooltip]"), function (el) {
        el.addEventListener("mouseenter", function () { showTooltip(el); });
        el.addEventListener("focus", function () { showTooltip(el); });
        el.addEventListener("mouseleave", hideTooltip);
        el.addEventListener("blur", hideTooltip);
    });

    if (body.getAttribute("data-page") === "profile") {
        setActive("profile");
    }

    if (body.getAttribute("data-page") === "dashboard") {
        var initial = root.getAttribute("data-view") || (window.location.hash || "#overview").slice(1);
        if (views.indexOf(initial) === -1) initial = "overview";
        showView(initial);
        var openSkill = new URLSearchParams(window.location.search).get("skill");
        if (openSkill) {
            var scope = document.getElementById(root.getAttribute("data-view") || "overview") || document;
            var match = scope.querySelector('.skill-toggle[data-skill="' + openSkill + '"]');
            if (match) setSkillCard(match.closest(".skill-card"), true);
        }
        window.addEventListener("hashchange", function () {
            var id = (window.location.hash || "#overview").slice(1);
            if (views.indexOf(id) !== -1) showView(id);
        });
    }

    var list = document.getElementById("resource-list");
    if (list && search) {
        var rows = Array.prototype.slice.call(list.querySelectorAll(".resource-row"));
        var diffSelect = document.getElementById("filter-difficulty");
        var catSelect = document.getElementById("filter-category");
        var empty = document.getElementById("filter-empty");
        var count = document.getElementById("resource-count");
        var form = document.getElementById("resource-search-form");

        function fill(select, attr) {
            if (!select) return;
            var values = [];
            rows.forEach(function (row) {
                var value = row.getAttribute(attr) || "";
                if (value && values.indexOf(value) === -1) values.push(value);
            });
            values.sort();
            var wrap = select.closest(".filter");
            if (!values.length) {
                if (wrap) wrap.hidden = true;
                return;
            }
            values.forEach(function (value) {
                var option = document.createElement("option");
                option.value = value;
                option.textContent = value;
                select.appendChild(option);
            });
        }

        function applyFilters() {
            var query = search.value.trim().toLowerCase();
            var difficulty = diffSelect ? diffSelect.value : "";
            var category = catSelect ? catSelect.value : "";
            var shown = 0;
            rows.forEach(function (row) {
                var haystack = (row.getAttribute("data-search") || "").toLowerCase();
                var visible = (!query || haystack.indexOf(query) !== -1)
                    && (!difficulty || row.getAttribute("data-difficulty") === difficulty)
                    && (!category || row.getAttribute("data-category") === category);
                row.hidden = !visible;
                if (visible) shown += 1;
            });
            if (count) count.textContent = "Showing " + shown + " of " + rows.length;
            if (empty) empty.hidden = shown !== 0;
        }

        fill(diffSelect, "data-difficulty");
        fill(catSelect, "data-category");
        search.addEventListener("input", function () {
            if (search.value.trim()) showView("learning-resources", { hash: true });
            applyFilters();
        });
        if (diffSelect) diffSelect.addEventListener("change", function () {
            showView("learning-resources", { hash: true });
            applyFilters();
        });
        if (catSelect) catSelect.addEventListener("change", function () {
            showView("learning-resources", { hash: true });
            applyFilters();
        });
        if (form) {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                showView("learning-resources", { hash: true });
                applyFilters();
            });
        }
        applyFilters();
    }
})();
