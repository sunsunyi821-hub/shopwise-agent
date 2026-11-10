import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
function normalizeMarkdownTables(text: string): string {
    const lines = text.replace(/\|\s+\|(?=:?-{3,})/g, "|\n|").split("\n");
    const isSeparator = (line: string | undefined) => !!line && /^\s*\|?\s*:?-{3,}/.test(line);
    const output: string[] = [];
    for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        const next = lines[index + 1];
        const isHeader = /^\s*\|.*\|\s*$/.test(line) && !isSeparator(line);
        if (isHeader && isSeparator(next)) {
            const headerCells = Math.max(1, line.split("|").slice(1, -1).length);
            const separatorCells = (next ?? "")
                .split("|")
                .slice(1, -1)
                .map((cell) => cell.trim())
                .filter(Boolean).length;
            if (separatorCells !== headerCells) {
                lines[index + 1] = "|" + "---|".repeat(headerCells);
            }
            if (output.length && output[output.length - 1].trim() !== "") {
                output.push("");
            }
        }
        output.push(line);
    }
    return output.join("\n");
}
export function Markdown({ children }: {
    children: string;
}) {
    return (<div className="markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdownTables(children)}</ReactMarkdown>
    </div>);
}
