(function () {
    var root = document.documentElement;
    var button = document.getElementById("theme-toggle");
    var menuBtn = document.getElementById("menu-toggle");
    var links = document.getElementById("site-links");

    function current() {
        return root.getAttribute("data-theme") === "light" ? "light" : "dark";
    }

    function paint(theme) {
        root.setAttribute("data-theme", theme);
        if (!button) return;
        var next = theme === "dark" ? "light" : "dark";
        button.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
        button.setAttribute("aria-label", "Switch to " + next + " theme");
    }

    paint(current());

    if (button) {
        button.addEventListener("click", function () {
            var next = current() === "dark" ? "light" : "dark";
            paint(next);
            try { localStorage.setItem("learnpath-theme", next); } catch (err) {}
        });
    }

    function setMenu(open) {
        if (!links || !menuBtn) return;
        links.classList.toggle("is-open", open);
        menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
        menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    }

    if (menuBtn && links) {
        menuBtn.addEventListener("click", function () {
            setMenu(menuBtn.getAttribute("aria-expanded") !== "true");
        });
        links.addEventListener("click", function (event) {
            if (event.target.tagName === "A") setMenu(false);
        });
    }

    var watched = false;

    function watchCards() {
        if (watched) return;
        watched = true;
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        if (!("IntersectionObserver" in window)) return;

        var nodes = document.querySelectorAll(".card, .steps li, .skill, .reasons li");
        Array.prototype.forEach.call(nodes, function (node, index) {
            node.style.opacity = "0";
            node.style.transform = "translateY(16px)";
            node.style.transitionDelay = (index % 4) * 70 + "ms";
        });

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                entry.target.style.transition = "opacity 0.6s ease, transform 0.6s ease";
                entry.target.style.opacity = "1";
                entry.target.style.transform = "none";
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.16, rootMargin: "0px 0px -40px 0px" });

        Array.prototype.forEach.call(nodes, function (node) { observer.observe(node); });
    }

    var intro = document.getElementById("site-intro");
    var word = document.getElementById("intro-word");
    var introDone = false;

    function blockIntroScroll(event) {
        event.preventDefault();
    }

    function lockIntroScroll() {
        document.addEventListener("wheel", blockIntroScroll, { passive: false });
        document.addEventListener("touchmove", blockIntroScroll, { passive: false });
    }

    function unlockIntroScroll() {
        document.removeEventListener("wheel", blockIntroScroll);
        document.removeEventListener("touchmove", blockIntroScroll);
    }

    function finishIntro() {
        if (introDone) return;
        introDone = true;
        unlockIntroScroll();
        if (intro && intro.parentNode) intro.parentNode.removeChild(intro);
        root.classList.remove("intro-pending", "intro-leaving");
        watchCards();
    }

    function playIntro() {
        if (!root.classList.contains("intro-pending") || !intro || !word) {
            finishIntro();
            return;
        }

        var failSafe = setTimeout(finishIntro, 7000);

        function reveal() {
            clearTimeout(failSafe);
            finishIntro();
        }

        function fadeHome() {
            root.classList.remove("intro-pending");
            root.classList.add("intro-leaving");
            intro.classList.add("is-leaving");
        }

        function park() {
            var target = document.querySelector(".nav .brand > span");
            if (!target) {
                fadeHome();
                setTimeout(reveal, 800);
                return;
            }
            var from = word.getBoundingClientRect();
            var to = target.getBoundingClientRect();
            var fromSize = parseFloat(window.getComputedStyle(word).fontSize) || 1;
            var toSize = parseFloat(window.getComputedStyle(target).fontSize) || fromSize;
            var scale = toSize / fromSize;
            var dx = Math.round(to.left - from.left);
            var dy = Math.round((to.top + to.height / 2) - (from.top + from.height / 2));
            word.classList.add("is-moving");
            window.requestAnimationFrame(function () {
                window.requestAnimationFrame(function () {
                    fadeHome();
                    word.style.transform = "translate(" + dx + "px, " + dy + "px) scale(" + scale + ")";
                });
            });
            var moved = false;
            function landed(event) {
                if (event && event.propertyName !== "transform") return;
                if (moved) return;
                moved = true;
                word.removeEventListener("transitionend", landed);
                reveal();
            }
            word.addEventListener("transitionend", landed);
            setTimeout(landed, 1000);
        }

        var wrote = false;
        function written(event) {
            if (wrote) return;
            if (event && event.animationName && event.animationName !== "intro-write") return;
            wrote = true;
            word.classList.add("is-written");
            setTimeout(park, 180);
        }

        word.addEventListener("animationend", written);
        lockIntroScroll();
        window.requestAnimationFrame(function () {
            word.classList.add("is-writing");
        });
        setTimeout(written, 1900);

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") finishIntro();
        });
    }

    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(playIntro);
    } else {
        playIntro();
    }

    if (!root.classList.contains("intro-pending")) watchCards();
})();
