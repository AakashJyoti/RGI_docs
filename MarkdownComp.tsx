import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/default.css";
import { useState } from "react";
import { getAllContent } from "../utils";

type Props = {
  markdownContent: string;
};

const MarkdownComp = ({ markdownContent }: Props) => {
  const [copied, setCopied] = useState<null | number>(null);

  const handleCopy = (code: React.ReactNode, index: number) => {
    const content = getAllContent(code);
    copyToClipboard(content);
    setCopied(index);
    setTimeout(() => setCopied(null), 2000);
  };

  const copyToClipboard = async (code: string) => {
    await navigator.clipboard.writeText(code);
  };

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight, rehypeRaw]}
      components={{
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        ),
        table: ({ children }) => (
          <table className="markdown-table">{children}</table>
        ),
        thead: ({ children }) => (
          <thead className="markdown-thead">{children}</thead>
        ),
        tbody: ({ children }) => (
          <tbody className="markdown-tbody">{children}</tbody>
        ),
        tr: ({ children }) => <tr className="markdown-tr">{children}</tr>,
        th: ({ children }) => <th className="markdown-th">{children}</th>,
        td: ({ children }) => <td className="markdown-td">{children}</td>,
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");

          let lineNumber = 0;
          if (node && node.position) {
            lineNumber = node.position.start.line;
          }

          return !inline && match ? (
            <div style={{ position: "relative" }}>
              <pre className={className} {...props}>
                <div className="flex mb-2">
                  <p className="bg-gray-300 rounded px-2 py-1">{match[1]}</p>
                </div>
                <code className={`language-${match[1]}`}>{children}</code>
              </pre>
              <button
                className={`absolute top-2 right-2 cursor-pointer rounded px-2 py-1 text-white border-none ${
                  copied ? "bg-green-500" : "bg-gray-400"
                }`}
                onClick={() => handleCopy(children, lineNumber)}
              >
                {copied === lineNumber ? "Copied!" : "Copy"}
              </button>
            </div>
          ) : (
            <code className={`${className} bg-slate-100`} {...props}>
              {children}
            </code>
          );
        },
      }}
    >
      {markdownContent}
    </ReactMarkdown>
  );
};
export default MarkdownComp;
