document.addEventListener("DOMContentLoaded", () => {
    // Define configuration variables for link handling
    const currentDomain = window.location.hostname;
    const excludedClasses = ['md-nav__link', 'md-footer__link', 'md-logo'];
    const fileExtensions = ['pdf', 'zip', 'tar', 'gz', 'exe', 'dmg', 'pkg'];

    /**
     * Selects all anchor elements (<a>) with an href attribute from the document.
     * @type {NodeListOf<HTMLAnchorElement>}
     */
    document.querySelectorAll('a[href]').forEach(link => {
        try {
            const url = new URL(link.href);

            // Check if the link is external
            if (url.hostname && url.hostname !== currentDomain && !excludedClasses.some(cls => link.classList.contains(cls))) {
                link.classList.add('external-link');
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }

            // Check if the link points to a file
            if (fileExtensions.some(ext => link.href.endsWith(`.${ext}`))) {
                link.target = '_blank';
            }
        } catch (e) {
            // Ignore invalid URLs (e.g., mailto:, javascript:, etc.)
            console.debug('Skipping invalid URL:', link.href);
        }
    });
});
