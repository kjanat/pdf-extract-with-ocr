/**
 * @fileoverview Link enhancement script for MkDocs Material theme.
 * Automatically handles external links and file downloads by adding appropriate
 * attributes and classes to anchor elements.
 *
 * Features:
 * - Opens external links in new tabs with security attributes
 * - Opens file downloads in new tabs
 * - Excludes navigation and footer links from external link processing
 *
 * @author kjanat
 * @version 1.0.0
 */

/**
 * Configuration for link handling.
 * @typedef {Object} LinkConfig
 * @property {string} currentDomain - The current domain of the site
 * @property {ReadonlyArray<string>} excludedClasses - CSS classes to exclude from external link processing
 * @property {ReadonlyArray<string>} fileExtensions - File extensions that should open in new tabs
 */

/**
 * Initializes link enhancement on DOM content loaded.
 * Processes all anchor elements and applies external link and file download handling.
 *
 * @listens DOMContentLoaded
 */
document.addEventListener("DOMContentLoaded", () => {
    /**
     * The current domain hostname.
     * @type {string}
     * @const
     */
    const currentDomain = window.location.hostname;

    /**
     * CSS classes to exclude from external link processing.
     * These are typically navigation, footer, and logo links.
     * @type {ReadonlyArray<string>}
     * @const
     */
    const excludedClasses = ['md-nav__link', 'md-footer__link', 'md-logo'];

    /**
     * File extensions that should open in a new tab.
     * @type {ReadonlyArray<string>}
     * @const
     */
    const fileExtensions = ['pdf', 'zip', 'tar', 'gz', 'exe', 'dmg', 'pkg'];

    /**
     * All anchor elements with href attributes in the document.
     * @type {NodeListOf<HTMLAnchorElement>}
     */
    const links = document.querySelectorAll('a[href]');

    /**
     * Processes each link to apply external link and file download handling.
     *
     * @param {HTMLAnchorElement} link - The anchor element to process
     */
    links.forEach(link => {
        try {
            /**
             * Parsed URL object from the link's href attribute.
             * @type {URL}
             */
            const url = new URL(link.href);

            /**
             * Checks if the link is external (different domain).
             * @type {boolean}
             */
            const isExternal = Boolean(url.hostname && url.hostname !== currentDomain);

            /**
             * Checks if the link has any excluded CSS classes.
             * @type {boolean}
             */
            const hasExcludedClass = excludedClasses.some(cls => link.classList.contains(cls));

            // Apply external link handling
            if (isExternal && !hasExcludedClass) {
                link.classList.add('external-link');
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }

            /**
             * Checks if the link points to a downloadable file.
             * @type {boolean}
             */
            const isFileDownload = fileExtensions.some(ext => link.href.endsWith(`.${ext}`));

            // Apply file download handling
            if (isFileDownload) {
                link.target = '_blank';
            }
        } catch (e) {
            /**
             * Error caught when parsing invalid URLs.
             * Invalid URLs include: mailto:, javascript:, tel:, etc.
             * @type {Error}
             */
            const error = /** @type {Error} */ (e);
            console.debug('Skipping invalid URL:', link.href, error.message);
        }
    });
});
