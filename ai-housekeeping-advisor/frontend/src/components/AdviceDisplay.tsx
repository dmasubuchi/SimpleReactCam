import React from 'react';
import { AdviceResponse } from '../types';
import '../styles/AdviceDisplay.css';
import ReactMarkdown from 'react-markdown';

interface AdviceDisplayProps {
  adviceResponse: AdviceResponse | null;
  isLoading: boolean;
}

/**
 * Component for displaying housekeeping advice.
 */
const AdviceDisplay: React.FC<AdviceDisplayProps> = ({ adviceResponse, isLoading }) => {
  if (isLoading) {
    return (
      <div className="advice-display loading">
        <div className="loading-spinner"></div>
        <p>Analyzing image and generating advice...</p>
      </div>
    );
  }

  if (!adviceResponse) {
    return (
      <div className="advice-display empty">
        <p>Upload an image to receive housekeeping advice</p>
      </div>
    );
  }

  const { advice, image_analysis } = adviceResponse;
  const { properties, labels } = image_analysis;

  return (
    <div className="advice-display">
      <div className="advice-header">
        <h2>Housekeeping Advice</h2>
        <div className="environment-info">
          <span className="environment-type">
            {properties.environment_type !== 'unknown' 
              ? `Environment: ${properties.environment_type}` 
              : 'Environment type not detected'}
          </span>
          <span className="cleanliness-level">
            {properties.cleanliness_level !== 'unknown' 
              ? `Cleanliness: ${properties.cleanliness_level}` 
              : ''}
          </span>
        </div>
      </div>
      
      <div className="advice-content">
        <ReactMarkdown className="advice-text">{advice}</ReactMarkdown>
      </div>
      
      <div className="analysis-details">
        <h3>Image Analysis</h3>
        <div className="detected-items">
          <h4>Detected Items:</h4>
          <ul className="labels-list">
            {labels.slice(0, 5).map((label, index) => (
              <li key={index}>
                {label.description} ({Math.round(label.score * 100)}%)
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdviceDisplay;
