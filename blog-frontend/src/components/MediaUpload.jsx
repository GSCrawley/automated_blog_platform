import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, Upload, Image, Video, Link, X } from 'lucide-react';

const MediaUpload = ({
  value = '',
  onChange,
  accept = 'image/*,video/*',
  maxSize = 10 * 1024 * 1024, // 10MB
  placeholder = 'Drop file here or click to browse',
  label = 'Media Upload'
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [previewUrl, setPreviewUrl] = useState(value);
  const [mode, setMode] = useState(value ? 'url' : 'upload'); // 'upload' or 'url'
  const fileInputRef = useRef(null);

  const handleUpload = useCallback(async (file) => {
    setUploading(true);
    setUploadProgress(0);
    setError('');

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);

      // Upload file
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'}/blog/upload-media`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }

      const result = await response.json();

      if (result.success) {
        const newUrl = result.url;
        setPreviewUrl(newUrl);
        onChange(newUrl);
        setMode('upload');
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload file. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onChange]);

  const handleFileSelect = useCallback(async (file) => {
    if (!file) return;

    // Validate file type
    const allowedTypes = accept.split(',').map(type => type.trim());
    const isAllowed = allowedTypes.some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });

    if (!isAllowed) {
      setError('File type not allowed. Please select an image or video file.');
      return;
    }

    // Validate file size
    if (file.size > maxSize) {
      setError(`File size exceeds ${(maxSize / (1024 * 1024)).toFixed(0)}MB limit.`);
      return;
    }

    setError('');
    await handleUpload(file);
  }, [accept, maxSize, handleUpload]);



  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleUrlChange = useCallback((newUrl) => {
    setPreviewUrl(newUrl);
    onChange(newUrl);
    setError('');
  }, [onChange]);

  const clearMedia = useCallback(() => {
    setPreviewUrl('');
    setError('');
    onChange('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onChange]);

  const getFileIcon = () => {
    if (!previewUrl) return null;

    const isVideo = previewUrl.match(/\.(mp4|webm|ogg|avi|mov)$/i) ||
                   previewUrl.includes('video');

    return isVideo ? <Video className="h-8 w-8 text-blue-500" /> :
                     <Image className="h-8 w-8 text-green-500" />;
  };

  const isImage = previewUrl && !previewUrl.match(/\.(mp4|webm|ogg|avi|mov)$/i) &&
                  !previewUrl.includes('video');

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <div className="flex items-center space-x-2">
          <Button
            type="button"
            variant={mode === 'upload' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('upload')}
          >
            <Upload className="h-4 w-4 mr-1" />
            Upload
          </Button>
          <Button
            type="button"
            variant={mode === 'url' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('url')}
          >
            <Link className="h-4 w-4 mr-1" />
            URL
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-400 text-red-700 px-3 py-2 rounded-md flex items-center text-sm">
          <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      {mode === 'upload' ? (
        <div className="space-y-2">
          {/* Upload Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              isDragOver
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            } ${uploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !uploading && fileInputRef.current?.click()}
          >
            {uploading ? (
              <div className="space-y-2">
                <div className="flex justify-center">
                  <Upload className="h-8 w-8 text-blue-500 animate-pulse" />
                </div>
                <p className="text-sm text-gray-600">Uploading...</p>
                <Progress value={uploadProgress} className="w-full" />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-center">
                  <Upload className="h-8 w-8 text-gray-400" />
                </div>
                <p className="text-sm text-gray-600">{placeholder}</p>
                <p className="text-xs text-gray-400">
                  Supports images and videos up to {(maxSize / (1024 * 1024)).toFixed(0)}MB
                </p>
              </div>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept={accept}
            onChange={handleFileInputChange}
            className="hidden"
          />

          {/* Preview */}
          {previewUrl && (
            <div className="relative border rounded-lg p-2 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getFileIcon()}
                  <span className="text-sm text-gray-700 truncate max-w-xs">
                    {previewUrl.split('/').pop()}
                  </span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={clearMedia}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              {isImage && (
                <div className="mt-2">
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="max-w-full max-h-32 object-contain rounded"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* URL Input Mode */
        <div className="space-y-2">
          <Input
            type="url"
            value={previewUrl}
            onChange={(e) => handleUrlChange(e.target.value)}
            placeholder="https://example.com/image.jpg"
          />

          {/* Preview for URL */}
          {previewUrl && (
            <div className="relative border rounded-lg p-2 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getFileIcon()}
                  <span className="text-sm text-gray-700 truncate max-w-xs">
                    {previewUrl}
                  </span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={clearMedia}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              {isImage && (
                <div className="mt-2">
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="max-w-full max-h-32 object-contain rounded"
                    onError={() => setError('Invalid image URL')}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MediaUpload;