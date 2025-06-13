import React from 'react';
import { Lightbulb, Code, Copy, CheckCircle } from 'lucide-react';

export interface Theme {
    name: string;
    description: string;
    boolean_query?: string;
    [key: string]: any; // Allow additional fields
}

interface ThemeDisplayProps {
    themes: Theme[];
    title?: string;
}

const ThemeDisplay: React.FC<ThemeDisplayProps> = ({
    themes,
    title = 'Discovered Themes',
}) => {
    const [copiedIndex, setCopiedIndex] = React.useState<number | null>(null);

    const copyToClipboard = async (text: string, index: number) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    const getConfidenceColor = (score?: number) => {
        if (!score) return 'gray';
        if (score >= 0.7) return 'green';
        if (score >= 0.5) return 'yellow';
        return 'red';
    };

    const getConfidenceLabel = (score?: number) => {
        if (!score) return 'Unknown';
        if (score >= 0.7) return 'High';
        if (score >= 0.5) return 'Medium';
        return 'Low';
    };

    if (!themes || themes.length === 0) {
        return (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
                <Lightbulb className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">No themes discovered yet.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center space-x-3 mb-6">
                <div className="p-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl">
                    <Lightbulb className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                    <p className="text-gray-600 text-sm">
                        {themes.length} theme{themes.length !== 1 ? 's' : ''}{' '}
                        discovered from your analysis
                    </p>
                </div>
            </div>

            {/* Themes Grid */}
            <div className="grid gap-6">
                {themes.map((theme, index) => (
                    <div
                        key={index}
                        className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
                    >
                        {/* Theme Header */}
                        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border-b border-gray-200 p-4">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2 leading-tight">
                                        {theme.name}
                                    </h3>
                                </div>
                                <div className="text-2xl font-bold text-purple-600 ml-4">
                                    #{index + 1}
                                </div>
                            </div>
                        </div>

                        {/* Theme Content */}
                        <div className="p-4 space-y-4">
                            {/* Description */}
                            <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-2 uppercase tracking-wide">
                                    Description
                                </h4>
                                <p className="text-gray-900 leading-relaxed bg-gray-50 p-3 rounded-lg border">
                                    {theme.description}
                                </p>
                            </div>

                            {/* Boolean Query */}
                            {theme.boolean_query && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <h4 className="text-sm font-medium text-gray-700 uppercase tracking-wide flex items-center space-x-1">
                                            <Code className="w-4 h-4" />
                                            <span>Boolean Query</span>
                                        </h4>
                                        <button
                                            onClick={() =>
                                                copyToClipboard(
                                                    theme.boolean_query || '',
                                                    index
                                                )
                                            }
                                            className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-700 transition-colors"
                                        >
                                            {copiedIndex === index ? (
                                                <>
                                                    <CheckCircle className="w-3 h-3" />
                                                    <span>Copied!</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Copy className="w-3 h-3" />
                                                    <span>Copy</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                    <div className="bg-gray-900 text-gray-100 p-3 rounded-lg font-mono text-sm overflow-x-auto border">
                                        <code>
                                            {theme.boolean_query ||
                                                'No query available'}
                                        </code>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Summary Footer */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-4 mt-6">
                <div className="flex items-center space-x-2 text-purple-700">
                    <CheckCircle className="w-5 h-5" />
                    <span className="font-medium">
                        Analysis completed with {themes.length} high-quality
                        theme{themes.length !== 1 ? 's' : ''} discovered
                    </span>
                </div>
                <p className="text-purple-600 text-sm mt-1">
                    Each theme includes a detailed description and optimized
                    boolean query for further analysis.
                </p>
            </div>
        </div>
    );
};

export default ThemeDisplay;
