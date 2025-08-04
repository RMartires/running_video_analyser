# Sports Video Analysis System

A comprehensive running form analysis system that uses computer vision and machine learning to analyze running videos, detect gait patterns, and provide detailed biomechanical insights.

## 🏃‍♂️ Features

### Core Analysis Engine
- **Pose Detection**: Uses MediaPipe to detect and track human pose landmarks
- **Gait Analysis**: Identifies foot strikes, stride patterns, and running cadence
- **Video Annotation**: Multiple annotation styles with detailed metrics overlay
- **Biomechanical Metrics**: Calculates stride length, ground contact time, and other key running metrics

### Web Application
- **Modern UI**: Clean, responsive Next.js frontend with Tailwind CSS
- **Video Upload**: Easy video upload and processing interface
- **Real-time Processing**: FastAPI backend for efficient video analysis
- **Cloud Storage**: Integrated with Supabase for scalable file management

### Automation & Processing
- **Background Processing**: Automated cron job processing for video analysis
- **Email Notifications**: Automatic email alerts when analysis is complete
- **Batch Processing**: Handle multiple videos efficiently

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- FFmpeg (for video processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sports_video
   ```

2. **Set up the Python environment**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the web application**
   ```bash
   # Backend
   cd webapp/backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../my-app
   npm install
   ```

4. **Configure environment variables**
   ```bash
   # In webapp/backend/.env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SUPABASE_BUCKET=your_bucket_name
   ```

### Running the System

1. **Start the backend server**
   ```bash
   cd webapp/backend
   uvicorn main:app --reload
   ```

2. **Start the frontend development server**
   ```bash
   cd webapp/my-app
   npm run dev
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🔧 Core Scripts

### Analysis Scripts
- **`running_analysis.py`** - Main analysis engine for detecting running patterns
- **`annotate_analysis.py`** - Creates annotated videos with detailed metrics
- **`annotate_with_opencv_pillow.py`** - Alternative annotation system
- **`annotate_landmarks.py`** - Pose landmark visualization
- **`annotate_analysis_moviepy.py`** - MoviePy-based video annotation

### Usage Examples

```bash
# Analyze a running video
python running_analysis.py path/to/video.mp4

# Create annotated output
python annotate_analysis.py path/to/video.mp4

# Process with landmarks overlay
python annotate_landmarks.py path/to/video.mp4
```

## 🤖 Automation Setup

### Cron Job Processing
The system includes automated processing capabilities:

```bash
# Set up cron job (see CRON_SETUP.md for details)
cd webapp/backend
./run_cron.sh
```

### Email Notifications
Configure email notifications for processing completion:

```bash
# See EMAIL_SETUP.md for configuration details
python send_email.py
```

## 📊 Analysis Metrics

The system provides comprehensive running analysis including:

- **Gait Metrics**
  - Foot strike patterns (heel, midfoot, forefoot)
  - Ground contact time
  - Flight time
  - Cadence (steps per minute)

- **Biomechanical Analysis**
  - Stride length and frequency
  - Vertical oscillation
  - Pose landmark tracking
  - Joint angle analysis

- **Visual Annotations**
  - Real-time metrics overlay
  - Pose skeleton visualization
  - Foot strike indicators
  - Performance graphs

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance web framework
- **MediaPipe** - Google's ML framework for pose detection
- **OpenCV** - Computer vision and video processing
- **NumPy** - Numerical computing
- **Supabase** - Cloud database and storage

### Frontend
- **Next.js 15** - React framework with server-side rendering
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Headless UI components

### Processing
- **PIL/Pillow** - Image processing
- **MoviePy** - Video editing and processing

## 📁 Project Structure

```
sports_video/
├── running_analysis.py          # Main analysis engine
├── annotate_analysis.py         # Video annotation
├── annotate_with_opencv_pillow.py
├── annotate_landmarks.py
├── annotate_analysis_moviepy.py
├── requirements.txt             # Python dependencies
├── videos/                      # Video files
├── mocks/                       # Mock data and images
├── font/                        # Font files for annotations
├── webapp/
│   ├── backend/                 # FastAPI backend
│   │   ├── main.py             # API endpoints
│   │   ├── cron_processor.py   # Automated processing
│   │   ├── send_email.py       # Email notifications
│   │   └── requirements.txt    # Backend dependencies
│   └── my-app/                 # Next.js frontend
│       ├── app/                # Next.js app directory
│       ├── components/         # React components
│       └── package.json        # Frontend dependencies
```

## 🔬 Analysis Pipeline

1. **Video Input** - Upload or select running video
2. **Pose Detection** - Extract body landmarks using MediaPipe
3. **Gait Analysis** - Analyze foot strikes and running patterns
4. **Metric Calculation** - Compute biomechanical metrics
5. **Visualization** - Generate annotated video with overlays
6. **Output** - Provide analysis results and annotated video

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

### System Requirements
- Linux/macOS/Windows
- Python 3.8+
- Node.js 18+
- 4GB+ RAM (8GB recommended for video processing)

### Python Dependencies
See `requirements.txt` and `webapp/backend/requirements.txt`

### Node.js Dependencies
See `webapp/my-app/package.json`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in the `webapp/backend/` directory
- Review setup guides: `CRON_SETUP.md` and `EMAIL_SETUP.md`
- Create an issue in the repository

## 🚀 Future Enhancements

- Real-time video processing
- Mobile app integration
- Advanced biomechanical analysis
- Multi-sport analysis support
- AI-powered coaching recommendations 