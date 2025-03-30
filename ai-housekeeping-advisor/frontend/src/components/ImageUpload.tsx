import React, { useState, useRef, ChangeEvent } from 'react';
import apiService from '../services/api';
import { AdviceResponse } from '../types';
import '../styles/ImageUpload.css';

interface ImageUploadProps {
  onAdviceReceived: (response: AdviceResponse) => void;
  onError: (error: Error) => void;
  onUploadStart?: () => void;
}

/**
 * Component for uploading and processing images.
 */
const ImageUpload: React.FC<ImageUploadProps> = ({ onAdviceReceived, onError, onUploadStart }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [context, setContext] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle file selection.
   */
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    
    if (file) {
      if (!file.type.startsWith('image/')) {
        onError(new Error('Please select an image file (JPEG, PNG, etc.)'));
        return;
      }
      
      setSelectedFile(file);
      
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setSelectedFile(null);
      setPreview(null);
    }
  };

  /**
   * Handle context input change.
   */
  const handleContextChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setContext(event.target.value);
  };

  /**
   * Handle image upload and processing.
   */
  const handleUpload = async () => {
    if (!selectedFile) {
      onError(new Error('Please select an image first'));
      return;
    }
    
    try {
      setIsUploading(true);
      if (onUploadStart) {
        onUploadStart();
      }
      const response = await apiService.analyzeImage(selectedFile, context || undefined);
      onAdviceReceived(response);
    } catch (error) {
      onError(error as Error);
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Reset the form.
   */
  const handleReset = () => {
    setSelectedFile(null);
    setPreview(null);
    setContext('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="image-upload">
      <div className="upload-container">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          ref={fileInputRef}
          disabled={isUploading}
          className="file-input"
          id="image-upload"
        />
        <label htmlFor="image-upload" className="file-label">
          {selectedFile ? 'Change Image' : 'Select Image'}
        </label>
        
        {preview && (
          <div className="image-preview">
            <img src={preview} alt="Preview" />
          </div>
        )}
        
        <div className="context-input">
          <label htmlFor="context">
            Additional Context (optional):
          </label>
          <textarea
            id="context"
            value={context}
            onChange={handleContextChange}
            placeholder="E.g., I'm looking for cleaning tips for my kitchen..."
            disabled={isUploading}
            rows={3}
          />
        </div>
        
        <div className="button-group">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="upload-button"
          >
            {isUploading ? 'Processing...' : 'Get Advice'}
          </button>
          
          <button
            onClick={handleReset}
            disabled={isUploading || (!selectedFile && !context)}
            className="reset-button"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImageUpload;
