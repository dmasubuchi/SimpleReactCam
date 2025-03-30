import React, { useState, useRef } from 'react';
import Webcam from 'react-webcam';
import * as tf from '@tensorflow/tfjs';

function App() {
  const webcamRef = useRef(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [prediction, setPrediction] = useState(null);

  const capture = async () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      console.log('Image captured:', imageSrc);
      
      const tensor = tf.tensor([1, 2, 3]);
      console.log('Tensor created:', tensor);
      tensor.dispose();
      
      setPrediction('Processing image...');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Simple React Camera</h1>
        <div className="webcam-container">
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            width={640}
            height={480}
          />
        </div>
        <button onClick={() => {
          setIsCapturing(true);
          capture();
          setTimeout(() => setIsCapturing(false), 1000);
        }}>
          {isCapturing ? 'Capturing...' : 'Capture Photo'}
        </button>
        {prediction && <p>Prediction: {prediction}</p>}
      </header>
    </div>
  );
}

export default App;
