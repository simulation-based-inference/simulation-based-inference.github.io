let blocks = document.querySelectorAll(".bibtex");

async function copyBibtex(block, button) {
    // Copy the bibtex inside <pre> to the clipboard
    let bibtex = block.querySelector("pre");
    try {
        await navigator.clipboard.writeText(bibtex.innerText);
        button.innerText = 'copied';
        setTimeout(() => { button.innerText = 'copy'; }, 2000);
    } catch (err) {
        console.error('Failed to copy text: ', err);
    }
}


blocks.forEach((block) => {

    if (navigator.clipboard) {

        // Add a copy button
        let button = document.createElement("button");
        button.innerText = 'copy';
        button.classList.add('copy-button', "button", "is-small");
        block.appendChild(button);

        button.addEventListener("click", async () => {
            await copyBibtex(block, button);
        });
    }
});
