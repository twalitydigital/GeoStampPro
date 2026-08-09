import { useState, useRef, useEffect } from 'react';
import piexif from 'piexifjs';
import './index.css';

function App() {
  const [status, setStatus] = useState('Idle');
  const [location, setLocation] = useState(null);
  const [mode, setMode] = useState('camera'); // 'camera' or 'preview'
  const [photoData, setPhotoData] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Initialize camera and geolocation
  useEffect(() => {
    if (mode === 'camera') {
      startCamera();
      getLocation();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [mode]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setStatus('Ready');
    } catch (err) {
      console.error(err);
      setStatus('Camera access denied');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
    }
  };

  const getLocation = () => {
    if (!navigator.geolocation) {
      setStatus('Geolocation not supported');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setLocation(pos.coords),
      (err) => setStatus('Location access denied'),
      { enableHighAccuracy: true }
    );
  };

  const toExifRational = (coordinate) => {
    const absCoord = Math.abs(coordinate);
    const degrees = Math.floor(absCoord);
    const minutes = Math.floor((absCoord - degrees) * 60);
    const seconds = Math.round(((absCoord - degrees) * 60 - minutes) * 60 * 100);
    return [[degrees, 1], [minutes, 1], [seconds, 100]];
  };

  const takePhoto = () => {
    if (!videoRef.current || !location) {
      setStatus('Waiting for GPS/Camera...');
      return;
    }
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // Draw Camera Image
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Draw Stamping UI (Background Panel)
    ctx.fillStyle = 'rgba(22, 28, 45, 0.7)';
    ctx.roundRect = function (x, y, w, h, r) {
      if (w < 2 * r) r = w / 2;
      if (h < 2 * r) r = h / 2;
      this.beginPath();
      this.moveTo(x+r, y);
      this.arcTo(x+w, y,   x+w, y+h, r);
      this.arcTo(x+w, y+h, x,   y+h, r);
      this.arcTo(x,   y+h, x,   y,   r);
      this.arcTo(x,   y,   x+w, y,   r);
      this.closePath();
      return this;
    }
    
    const panelHeight = canvas.height * 0.15;
    ctx.roundRect(20, canvas.height - panelHeight - 20, canvas.width - 40, panelHeight, 20);
    ctx.fill();

    // Draw Text
    ctx.fillStyle = '#00ffcc';
    ctx.font = 'bold 36px "Outfit", sans-serif';
    ctx.fillText('GeoStamped', 40, canvas.height - panelHeight + 30);
    
    ctx.fillStyle = '#ffffff';
    ctx.font = '24px "Outfit", sans-serif';
    ctx.fillText(`LAT: ${location.latitude.toFixed(6)}`, 40, canvas.height - panelHeight + 80);
    ctx.fillText(`LNG: ${location.longitude.toFixed(6)}`, 40, canvas.height - panelHeight + 115);
    ctx.fillText(new Date().toLocaleString(), 40, canvas.height - panelHeight + 150);

    // Extract JPEG Data
    const jpegDataUrl = canvas.toDataURL('image/jpeg', 0.95);

    // Inject EXIF (GPS Data)
    try {
      const latRef = location.latitude >= 0 ? "N" : "S";
      const lngRef = location.longitude >= 0 ? "E" : "W";
      
      const exifObj = {
        "0th": {
          [piexif.ImageIFD.Software]: "GeoStamp Mobile Web",
        },
        "GPS": {
          [piexif.GPSIFD.GPSLatitudeRef]: latRef,
          [piexif.GPSIFD.GPSLatitude]: toExifRational(location.latitude),
          [piexif.GPSIFD.GPSLongitudeRef]: lngRef,
          [piexif.GPSIFD.GPSLongitude]: toExifRational(location.longitude),
        }
      };
      
      const exifBytes = piexif.dump(exifObj);
      const stampedJpeg = piexif.insert(exifBytes, jpegDataUrl);
      
      setPhotoData(stampedJpeg);
      setMode('preview');
      setStatus('Photo captured & geotagged!');
    } catch (e) {
      console.error(e);
      setStatus('EXIF preservation failed');
    }
  };

  const handleDownload = () => {
    if (!photoData) return;
    const a = document.createElement('a');
    a.href = photoData;
    a.download = `GeoStamped_${new Date().getTime()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <>
      <header>
        <h1>GeoStamp Mobile</h1>
        <p>Lightweight Progressive Web App</p>
      </header>

      <main className="card">
        {status && (
          <div className={`status-badge ${status.includes('denied') ? 'error' : ''}`}>
            {status}
          </div>
        )}

        <div className="preview-container">
          {mode === 'camera' ? (
            <>
              <video ref={videoRef} autoPlay playsInline muted />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
              {!location && <span>Acquiring GPS Signal...</span>}
            </>
          ) : (
            <img src={photoData} alt="Captured" />
          )}
        </div>

        <div className="button-group">
          {mode === 'camera' ? (
            <button className="btn primary" onClick={takePhoto}>
              📸 Capture Photo
            </button>
          ) : (
            <>
              <button className="btn primary" onClick={handleDownload}>
                💾 Save to Device
              </button>
              <button className="btn" onClick={() => setMode('camera')}>
                🔄 Take Another
              </button>
            </>
          )}
        </div>
      </main>
    </>
  );
}

export default App;
