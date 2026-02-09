export interface ParsedAttachment {
    filename: string;
    id: string;
}

export interface ParsedMessage {
    cleanText: string;
    attachments: ParsedAttachment[];
}

export function parseAttachments(text: string): ParsedMessage {
    const attachmentRegex = /\[Attached File: (.*?) \(ID: (.*?)\)\]/g;
    const attachments: ParsedAttachment[] = [];
    let match;

    // Find all matches
    while ((match = attachmentRegex.exec(text)) !== null) {
        attachments.push({ filename: match[1], id: match[2] });
    }

    // Remove from text
    const cleanText = text.replace(attachmentRegex, '').trim();
    return { cleanText, attachments };
}
