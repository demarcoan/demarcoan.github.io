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