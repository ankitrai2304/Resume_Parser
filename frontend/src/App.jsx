import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, XCircle, Loader, Download, Trash2 } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function App() {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  const [parsing, setParsing] = useState(false);
  const [results, setResults] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (fileList) => {
    const newFiles = Array.from(fileList).filter(file => {
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      return validTypes.includes(file.type);
    });

    setFiles(prev => [...prev, ...newFiles]);
    setResults(null);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setResults(null);
  };

  const clearAll = () => {
    setFiles([]);
    setResults(null);
  };

  const parseResumes = async () => {
    setParsing(true);
    setResults(null);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_URL}/api/parse-resumes-batch`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to parse resumes');
      }

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error parsing resumes. Please ensure backend is running on ' + API_URL);
    } finally {
      setParsing(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const downloadJSON = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `parsed-resumes-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-2">
            Resume Parser
          </h1>
          <p className="text-gray-600 text-sm md:text-base">
            Upload resumes and extract structured data instantly with AI-powered parsing
          </p>
        </div>

        {/* Main Upload Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-6">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".pdf,.doc,.docx"
              onChange={handleChange}
              className="hidden"
            />

            <label
              htmlFor="file-upload"
              className={`flex flex-col items-center justify-center w-full h-48 md:h-64 border-3 border-dashed rounded-xl cursor-pointer transition-all duration-300 ${dragActive
                  ? 'border-indigo-500 bg-indigo-50 scale-105'
                  : 'border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-indigo-400'
                }`}
            >
              <div className="flex flex-col items-center justify-center p-4">
                <Upload className={`w-12 h-12 md:w-16 md:h-16 mb-4 transition-colors ${dragActive ? 'text-indigo-500' : 'text-gray-400'}`} />
                <p className="mb-2 text-base md:text-lg font-semibold text-gray-700 text-center">
                  <span className="text-indigo-600">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs md:text-sm text-gray-500 text-center">
                  PDF, DOC, DOCX files supported (Max 10MB per file)
                </p>
              </div>
            </label>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-700">
                  Uploaded Files ({files.length})
                </h3>
                <button
                  onClick={clearAll}
                  className="flex items-center space-x-1 text-red-600 hover:text-red-700 text-sm font-medium"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Clear All</span>
                </button>
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 md:p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-indigo-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <FileText className="w-6 h-6 md:w-8 md:h-8 text-indigo-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-700 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="ml-4 p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
                      aria-label="Remove file"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Parse Button */}
          {files.length > 0 && (
            <div className="mt-6">
              <button
                onClick={parseResumes}
                disabled={parsing}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 md:py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                {parsing ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    <span>Parsing {files.length} Resume{files.length > 1 ? 's' : ''}...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    <span>Parse {files.length} Resume{files.length > 1 ? 's' : ''}</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Results Card */}
        {results && (
          <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-6 animate-fadeIn">
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-8 h-8 text-green-500 flex-shrink-0" />
                <div>
                  <h3 className="text-xl font-bold text-gray-800">Parsing Complete!</h3>
                  <p className="text-sm text-gray-600">
                    <span className="text-green-600 font-semibold">{results.successful}</span> successful,{' '}
                    <span className="text-red-600 font-semibold">{results.failed}</span> failed out of{' '}
                    <span className="font-semibold">{results.total_files}</span> files
                  </p>
                </div>
              </div>
              <button
                onClick={downloadJSON}
                className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 md:px-5 md:py-3 rounded-lg transition-colors shadow-md hover:shadow-lg"
              >
                <Download className="w-4 h-4" />
                <span className="font-medium">Download JSON</span>
              </button>
            </div>

            <div className="space-y-4">
              {results.results.map((result, index) => (
                <div
                  key={index}
                  className={`p-4 md:p-6 rounded-xl border-2 transition-all hover:shadow-md ${result.success
                      ? 'border-green-200 bg-green-50 hover:border-green-300'
                      : 'border-red-200 bg-red-50 hover:border-red-300'
                    }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <FileText className="w-5 h-5 text-gray-600 flex-shrink-0" />
                      <span className="font-semibold text-gray-800 truncate">{result.filename}</span>
                    </div>
                    {result.success ? (
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 ml-2" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 ml-2" />
                    )}
                  </div>

                  {result.success ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1 font-medium">Name</p>
                          <p className="text-sm font-semibold text-gray-800">{result.parsed_data.name}</p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1 font-medium">Email</p>
                          <p className="text-sm font-semibold text-gray-800 break-all">{result.parsed_data.email}</p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1 font-medium">Phone</p>
                          <p className="text-sm font-semibold text-gray-800">{result.parsed_data.phone}</p>
                        </div>
                        <div className="bg-white p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1 font-medium">Experience</p>
                          <p className="text-sm font-semibold text-gray-800">{result.parsed_data.experience}</p>
                        </div>
                      </div>

                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-2 font-medium">Skills ({result.parsed_data.skills.length})</p>
                        {result.parsed_data.skills.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {result.parsed_data.skills.map((skill, i) => (
                              <span
                                key={i}
                                className="px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 italic">No skills detected</p>
                        )}
                      </div>

                      <div className="bg-white p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-2 font-medium">Education</p>
                        {result.parsed_data.education.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {result.parsed_data.education.map((edu, i) => (
                              <span
                                key={i}
                                className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full"
                              >
                                {edu}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 italic">No education information found</p>
                        )}
                      </div>

                      <div className="bg-white p-3 rounded-lg border-l-4 border-indigo-500">
                        <p className="text-xs text-gray-500 mb-1 font-medium">Google Sheets Status</p>
                        <p className={`text-sm font-semibold ${result.parsed_data.sheets_status === 'success' ? 'text-green-600' : 'text-red-600'
                          }`}>
                          {result.parsed_data.sheets_status === 'success' ? '✓ Saved to Google Sheets' : result.parsed_data.sheets_status}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white p-4 rounded-lg">
                      <p className="text-sm text-red-600 font-medium">❌ {result.error}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-indigo-600 font-semibold mb-2 text-lg">📄 Supported Formats</div>
            <div className="text-sm text-gray-600">PDF, DOC, DOCX files up to 10MB each</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-indigo-600 font-semibold mb-2 text-lg">⚡ Fast Processing</div>
            <div className="text-sm text-gray-600">Parse multiple resumes instantly with AI</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-indigo-600 font-semibold mb-2 text-lg">☁️ Auto Save</div>
            <div className="text-sm text-gray-600">Data automatically saved to Google Sheets</div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Powered by FastAPI & React • Data secured with Google Service Account</p>
        </div>
      </div>
    </div>
  );
}