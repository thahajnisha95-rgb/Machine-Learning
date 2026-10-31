(function () {
    function cookieValue(name) {
        var parts = ("; " + document.cookie).split("; " + name + "=");
        if (parts.length < 2) return "";
        return decodeURIComponent(parts.pop().split(";").shift() || "");
    }
    function syncCsrf(form) {
        var token = cookieValue("csrftoken");
        var input = form && form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (token && input) input.value = token;
    }
    window.addEventListener("pageshow", function (event) {
        if (event.persisted) window.location.reload();
    });
    Array.prototype.forEach.call(document.querySelectorAll("form[method='post'], form[method='POST']"), function (form) {
        syncCsrf(form);
        form.addEventListener("submit", function () { syncCsrf(form); });
    });

    var form = document.getElementById("survey-form");
    var firstField = document.querySelector(
        ".survey-input, .survey-years input:checked, .survey-years input, .survey-chip-check input"
    );
    if (firstField && typeof firstField.focus === "function") {
        firstField.focus();
        if (firstField.select && firstField.type === "text") {
            firstField.select();
        }
    }
    if (!form) return;

    Array.prototype.forEach.call(document.querySelectorAll("[data-fill]"), function (chip) {
        chip.addEventListener("click", function () {
            var field = document.getElementById(chip.getAttribute("data-fill"));
            if (!field) return;
            field.value = chip.getAttribute("data-value") || "";
            field.focus();
        });
    });

    form.addEventListener("submit", function (event) {
        var action = (event.submitter && event.submitter.value) || "next";
        if (action === "back") return;

        var interestBoxes = form.querySelectorAll('input[name="interest"]');
        if (!interestBoxes.length) return;
        var extra = form.querySelector("#interest_extra");
        var picked = Array.prototype.some.call(interestBoxes, function (box) {
            return box.checked;
        });
        if (picked || (extra && extra.value.trim())) return;

        event.preventDefault();
        var alertNode = document.getElementById("survey-error");
        if (!alertNode) {
            alertNode = document.createElement("p");
            alertNode.className = "survey-error";
            alertNode.id = "survey-error";
            alertNode.setAttribute("role", "alert");
            form.parentNode.insertBefore(alertNode, form);
        }
        alertNode.hidden = false;
        alertNode.textContent = "Please pick at least one interest so we can match skills and courses.";
    });
})();
