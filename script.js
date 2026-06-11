// Questo messaggio appare nella console del browser.
// Serve solo per verificare che il file JavaScript sia collegato correttamente.

console.log("The website has loaded correctly.");

document.querySelectorAll("[data-include]").forEach(element => {
    const file = element.getAttribute("data-include");

    fetch(file)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Errore nel caricamento di ${file}`);
            }
            return response.text();
        })
        .then(html => {
            element.innerHTML = html;
        })
        .catch(error => console.error(error));
});



document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("image-modal");
    const modalImg = document.getElementById("modal-img");
    const closeModal = document.querySelector(".image-modal-close");

    if (!modal || !modalImg || !closeModal) {
        console.warn("Modal elements not found.");
        return;
    }

    document.querySelectorAll(".news-img").forEach(img => {
        img.addEventListener("click", () => {
            modal.style.display = "flex";
            modalImg.src = img.src;
            modalImg.alt = img.alt;
        });
    });

    closeModal.addEventListener("click", () => {
        modal.style.display = "none";
    });

    modal.addEventListener("click", event => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const pdfModal = document.getElementById("pdf-modal");
    const pdfFrame = document.getElementById("pdf-modal-frame");
    const pdfClose = document.querySelector(".pdf-modal-close");

    if (!pdfModal || !pdfFrame || !pdfClose) {
        return;
    }

    document.querySelectorAll(".certificate-link").forEach(button => {
        button.addEventListener("click", () => {
            const pdfPath = button.getAttribute("data-pdf");

            pdfFrame.src = pdfPath;
            pdfModal.style.display = "flex";
        });
    });

    pdfClose.addEventListener("click", () => {
        pdfModal.style.display = "none";
        pdfFrame.src = "";
    });

    pdfModal.addEventListener("click", event => {
        if (event.target === pdfModal) {
            pdfModal.style.display = "none";
            pdfFrame.src = "";
        }
    });
});