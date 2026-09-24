import { marked } from "marked";
import DOMPurify from "dompurify";

export function MarkdownMessage({ content }: { content: string }) {
  const html = DOMPurify.sanitize(marked.parse(content, { async: false }) as string);
  return (
    <div
      className="markdown-content"
      style={{ lineHeight: 1.5 }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
