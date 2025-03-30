import { useState } from 'react';
import './styles/App.css';
import ImageUpload from './components/ImageUpload';
import AdviceDisplay from './components/AdviceDisplay';
import { AdviceResponse } from './types';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adviceResponse, setAdviceResponse] = useState<AdviceResponse | null>(null);

  const handleAdviceReceived = (response: AdviceResponse) => {
    setAdviceResponse(response);
    setIsLoading(false);
    setError(null);
  };

  const handleError = (error: Error) => {
    setError(error.message);
    setIsLoading(false);
  };
  
  const handleUploadStart = () => {
    setIsLoading(true);
    setError(null);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>AI Housekeeping Advisor</h1>
        <p>Upload an image of your home environment to receive practical housekeeping advice</p>
      </header>
      
      <main className="app-main">
        <ImageUpload 
          onAdviceReceived={handleAdviceReceived} 
          onError={handleError}
          onUploadStart={handleUploadStart}
        />
        
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        
        <AdviceDisplay 
          adviceResponse={adviceResponse} 
          isLoading={isLoading} 
        />
      </main>
      
      <footer className="app-footer">
        <p>AI Housekeeping Advisor &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}

export default App;
