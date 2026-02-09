import { BBox } from '@/lib/api/chat';

export interface HighlightOptions {
    color?: string;
    duration?: number; // Auto-fade duration in ms
}

/**
 * Highlight a region in a PDF viewer based on bbox coordinates
 */
export function highlightPDFRegion(
    viewerElement: HTMLElement,
    bbox: BBox,
    options: HighlightOptions = {}
): () => void {
    const { color = 'rgba(255, 255, 0, 0.3)', duration = 3000 } = options;

    if (!bbox.page || bbox.x === undefined || bbox.y === undefined) {
        console.warn('Invalid PDF bbox:', bbox);
        return () => { };
    }

    // Create highlight overlay
    const highlight = document.createElement('div');
    highlight.style.position = 'absolute';
    highlight.style.left = `${bbox.x}px`;
    highlight.style.top = `${bbox.y}px`;
    highlight.style.width = `${bbox.width || 100}px`;
    highlight.style.height = `${bbox.height || 20}px`;
    highlight.style.backgroundColor = color;
    highlight.style.pointerEvents = 'none';
    highlight.style.zIndex = '1000';
    highlight.style.transition = 'opacity 0.5s';
    highlight.style.opacity = '1';

    // Find page container and add highlight
    const pageContainer = viewerElement.querySelector(
        `[data-page-number="${bbox.page}"]`
    );

    if (pageContainer) {
        pageContainer.appendChild(highlight);

        // Scroll to highlight
        highlight.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Auto-fade and remove
        const cleanup = () => {
            highlight.style.opacity = '0';
            setTimeout(() => {
                highlight.remove();
            }, 500);
        };

        if (duration > 0) {
            setTimeout(cleanup, duration);
        }

        return cleanup;
    }

    return () => { };
}

/**
 * Highlight text in an HTML/web document using selector or xpath
 */
export function highlightHTMLElement(
    element: Element,
    options: HighlightOptions = {}
): () => void {
    const { color = 'rgba(255, 255, 0, 0.3)', duration = 3000 } = options;

    const originalBackground = (element as HTMLElement).style.backgroundColor;
    const originalTransition = (element as HTMLElement).style.transition;

    (element as HTMLElement).style.backgroundColor = color;
    (element as HTMLElement).style.transition = 'background-color 0.3s';

    // Scroll to element
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });

    const cleanup = () => {
        (element as HTMLElement).style.backgroundColor = originalBackground;
        (element as HTMLElement).style.transition = originalTransition;
    };

    if (duration > 0) {
        setTimeout(cleanup, duration);
    }

    return cleanup;
}

/**
 * Highlight based on BBox configuration
 */
export function highlightBBox(
    containerElement: HTMLElement,
    bbox: BBox,
    options: HighlightOptions = {}
): () => void {
    // PDF highlighting
    if (bbox.page !== undefined) {
        return highlightPDFRegion(containerElement, bbox, options);
    }

    // HTML selector highlighting
    if (bbox.selector) {
        const element = containerElement.querySelector(bbox.selector);
        if (element) {
            return highlightHTMLElement(element, options);
        }
    }

    // XPath highlighting
    if (bbox.xpath) {
        const result = document.evaluate(
            bbox.xpath,
            containerElement,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        );
        if (result.singleNodeValue) {
            return highlightHTMLElement(result.singleNodeValue as Element, options);
        }
    }

    console.warn('Could not highlight bbox:', bbox);
    return () => { };
}
