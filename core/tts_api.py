import os
import re
import logging
import uuid
import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator, Union, Tuple
import io
import tempfile
import wave
import time
import threading
from pathlib import Path

import torch
import numpy as np
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import Kokoro TTS
from kokoro import KPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tts_api")

# --- Pydantic Models ---

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    stream: bool = False
    session_id: Optional[str] = None

class TTSResponse(BaseModel):
    session_id: Optional[str] = None
    audio_url: str
    message: str

class SessionRequest(BaseModel):
    voice: Optional[str] = "af_heart"

class SessionResponse(BaseModel):
    session_id: str
    message: str

# --- TTS Service ---

class TTSService:
    """Manages TTS processing and sessions"""
    
    def __init__(self, voices_dir: Optional[str] = None, lang_code: str = 'a'):
        """
        Initialize the TTS service
        
        Args:
            voices_dir: Directory containing voice models
            lang_code: Language code for Kokoro
        """
        self.lang_code = lang_code
        self.voices_dir = voices_dir
        self.sample_rate = 24000
        
        # Initialize TTS pipeline
        logger.info(f"Initializing Kokoro TTS pipeline with lang_code={lang_code}")
        self.pipeline = KPipeline(lang_code=lang_code)
        
        # Find available voices
        self.available_voices = self._get_available_voices()
        logger.info(f"Available voices: {', '.join(self.available_voices)}")
        
        # Sessions storage
        self.sessions = {}
        self.audio_cache = {}  # Cache for generated audio
        
        # Cache directory for audio files
        self.cache_dir = os.path.join(tempfile.gettempdir(), "kokoro_tts_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Audio cache directory: {self.cache_dir}")
        
        # Start cleanup thread for old audio files
        self.cleanup_thread = threading.Thread(target=self._cleanup_cache, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("TTS service initialized")
    
    def _get_available_voices(self) -> List[str]:
        """Get list of available voice models"""
        # Default voices in Kokoro
        default_voices = ["af_heart", "en_us_1", "en_us_2"]
        
        # Additional voices from voices_dir
        if self.voices_dir and os.path.isdir(self.voices_dir):
            custom_voices = []
            for voice_file in os.listdir(self.voices_dir):
                if voice_file.endswith(".pt"):
                    voice_name = os.path.splitext(voice_file)[0]
                    custom_voices.append(voice_name)
            
            if custom_voices:
                logger.info(f"Found {len(custom_voices)} custom voices: {', '.join(custom_voices)}")
                return default_voices + custom_voices
        
        return default_voices
    
    def _cleanup_cache(self):
        """Clean up old audio files from cache"""
        while True:
            try:
                # Sleep for 10 minutes
                time.sleep(600)
                
                # Get current time
                current_time = time.time()
                
                # Delete files older than 1 hour
                for file_path in os.listdir(self.cache_dir):
                    full_path = os.path.join(self.cache_dir, file_path)
                    
                    if os.path.isfile(full_path):
                        # Get file modification time
                        mod_time = os.path.getmtime(full_path)
                        
                        # Delete if older than 1 hour
                        if current_time - mod_time > 3600:
                            os.remove(full_path)
                            logger.debug(f"Deleted old cache file: {file_path}")
                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def create_session(self, voice: str = "af_heart") -> str:
        """
        Create a new TTS session
        
        Args:
            voice: Voice to use for this session
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Validate voice
        if voice not in self.available_voices:
            logger.warning(f"Requested voice '{voice}' not available, using default voice 'af_heart'")
            voice = "af_heart"
        
        # Initialize session data
        self.sessions[session_id] = {
            "voice": voice,
            "last_chunk": "",
            "pending_text": "",
            "last_access": time.time()
        }
        
        logger.info(f"Created session: {session_id} with voice: {voice}")
        return session_id
    
    def _split_by_punctuation(self, text: str) -> List[str]:
        """
        Split text into chunks at punctuation marks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Regex for splitting at punctuation marks followed by space or end of string
        chunks = re.split(r'([.!?;:,](?:\s|$))', text)
        
        # Combine punctuation with preceding text
        result = []
        for i in range(0, len(chunks) - 1, 2):
            if i + 1 < len(chunks):
                result.append(chunks[i] + chunks[i + 1])
            else:
                result.append(chunks[i])
        
        # Add last chunk if there's an odd number of chunks
        if len(chunks) % 2 == 1:
            result.append(chunks[-1])
        
        # Filter out empty chunks
        return [chunk for chunk in result if chunk.strip()]
    
    async def process_text(self, 
                        text: str,
                        voice: str = "af_heart",
                        speed: float = 1.0,
                        session_id: Optional[str] = None,
                        stream: bool = False) -> Union[str, AsyncGenerator[bytes, None]]:
        """
        Process text with TTS
        
        Args:
            text: Text to process
            voice: Voice to use
            speed: Speech speed
            session_id: Optional session ID
            stream: Whether to stream audio chunks
            
        Returns:
            Path to audio file or streaming audio generator
        """
        # Validate voice
        if voice not in self.available_voices:
            logger.warning(f"Requested voice '{voice}' not available, using default voice 'af_heart'")
            voice = "af_heart"
        
        # Get or create session
        if session_id:
            if session_id not in self.sessions:
                logger.info(f"Creating new session {session_id}")
                self.create_session(voice)
            
            # Update session
            session = self.sessions[session_id]
            session["last_access"] = time.time()
            voice = session["voice"]  # Use session voice
            
            # Add text to pending text
            pending_text = session["pending_text"] + text
            session["pending_text"] = pending_text
        else:
            # No session, just use the provided text
            pending_text = text
        
        if stream:
            # For streaming, we'll process text in chunks at punctuation marks
            async def stream_generator():
                # Split text into chunks at punctuation marks
                chunks = self._split_by_punctuation(pending_text)
                
                # Process chunks
                for i, chunk in enumerate(chunks):
                    try:
                        # Skip empty chunks
                        if not chunk.strip():
                            continue
                        
                        # Process this chunk
                        generator = self.pipeline(chunk, voice=voice, speed=speed)
                        
                        # Process each segment in the generator
                        for _, _, audio in generator:
                            # Convert to WAV format
                            with io.BytesIO() as buffer:
                                with wave.open(buffer, 'wb') as wf:
                                    wf.setnchannels(1)  # Mono
                                    wf.setsampwidth(2)  # 16-bit
                                    wf.setframerate(self.sample_rate)
                                    
                                    # Convert to int16
                                    audio_np = audio.numpy()
                                    int16_data = (audio_np * 32767).astype(np.int16)
                                    wf.writeframes(int16_data.tobytes())
                                
                                # Get the WAV data
                                buffer.seek(0)
                                yield buffer.read()
                        
                        # Update session if using one
                        if session_id and session_id in self.sessions:
                            session = self.sessions[session_id]
                            
                            # Update last chunk
                            session["last_chunk"] = chunk
                            
                            # Remove processed text from pending text
                            if i == len(chunks) - 1:
                                # Last chunk, clear pending text
                                session["pending_text"] = ""
                            else:
                                # Remove the processed chunk from pending text
                                session["pending_text"] = session["pending_text"][len(chunk):]
                        
                    except Exception as e:
                        logger.error(f"Error streaming chunk: {e}")
                        # Continue with next chunk
                        continue
                        
            # Return the async generator
            return stream_generator()
        else:
            # For non-streaming, process all text at once
            return await self._process_full_text(pending_text, voice, speed, session_id)
    
    async def _process_full_text(self, text: str, voice: str, speed: float, session_id: Optional[str] = None) -> str:
        """
        Process full text and save to a file
        
        Args:
            text: Text to process
            voice: Voice to use
            speed: Speech speed
            session_id: Optional session ID
            
        Returns:
            Path to the audio file
        """
        # Create a unique file name
        file_id = str(uuid.uuid4())
        file_path = os.path.join(self.cache_dir, f"{file_id}.wav")
        
        # Process the text
        try:
            # Create full audio
            audio_segments = []
            
            # Generate audio in a separate thread to avoid blocking
            def generate_audio():
                generator = self.pipeline(text, voice=voice, speed=speed)
                for _, _, audio in generator:
                    audio_segments.append(audio.numpy())
            
            # Run generation in thread
            thread = threading.Thread(target=generate_audio)
            thread.start()
            thread.join()
            
            # Combine all segments
            if audio_segments:
                full_audio = np.concatenate(audio_segments)
                
                # Write to WAV file
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.sample_rate)
                    
                    # Convert to int16
                    int16_data = (full_audio * 32767).astype(np.int16)
                    wf.writeframes(int16_data.tobytes())
                
                logger.info(f"Generated audio file: {file_path}")
                
                # Clear session pending text if using a session
                if session_id and session_id in self.sessions:
                    self.sessions[session_id]["pending_text"] = ""
                
                return file_path
            else:
                raise Exception("No audio generated")
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise
    
    async def _stream_text(self, text: str, voice: str, speed: float, session_id: Optional[str] = None) -> AsyncGenerator[bytes, None]:
        """
        Stream text as audio chunks
        
        Args:
            text: Text to process
            voice: Voice to use
            speed: Speech speed
            session_id: Optional session ID
            
        Yields:
            Audio data chunks
        """
        # Split text into chunks at punctuation marks
        chunks = self._split_by_punctuation(text)
        
        # Process chunks
        for i, chunk in enumerate(chunks):
            try:
                # Skip empty chunks
                if not chunk.strip():
                    continue
                
                # Process this chunk
                generator = self.pipeline(chunk, voice=voice, speed=speed)
                
                # Process each segment in the generator
                for _, _, audio in generator:
                    # Convert to WAV format
                    with io.BytesIO() as buffer:
                        with wave.open(buffer, 'wb') as wf:
                            wf.setnchannels(1)  # Mono
                            wf.setsampwidth(2)  # 16-bit
                            wf.setframerate(self.sample_rate)
                            
                            # Convert to int16
                            audio_np = audio.numpy()
                            int16_data = (audio_np * 32767).astype(np.int16)
                            wf.writeframes(int16_data.tobytes())
                        
                        # Get the WAV data
                        buffer.seek(0)
                        yield buffer.read()
                
                # Update session if using one
                if session_id and session_id in self.sessions:
                    session = self.sessions[session_id]
                    
                    # Update last chunk
                    session["last_chunk"] = chunk
                    
                    # Remove processed text from pending text
                    if i == len(chunks) - 1:
                        # Last chunk, clear pending text
                        session["pending_text"] = ""
                    else:
                        # Remove the processed chunk from pending text
                        session["pending_text"] = session["pending_text"][len(chunk):]
                
            except Exception as e:
                logger.error(f"Error streaming chunk: {e}")
                # Continue with next chunk
                continue
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information
        """
        if session_id not in self.sessions:
            return {"error": f"Session {session_id} not found"}
            
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "voice": session["voice"],
            "last_access": session["last_access"],
            "pending_text_length": len(session["pending_text"])
        }

# --- FastAPI App ---

app = FastAPI(
    title="TTS API",
    description="API for text-to-speech using Kokoro TTS",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global TTS service instance
tts_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize TTS service on startup"""
    global tts_service
    # Get voices directory from environment or use default
    voices_dir = os.environ.get("TTS_VOICES_DIR", None)
    lang_code = os.environ.get("TTS_LANG_CODE", "a")
    tts_service = TTSService(voices_dir=voices_dir, lang_code=lang_code)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "TTS API is running"}

@app.get("/voices")
async def list_voices():
    """Get list of available voices"""
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not initialized")
        
    return {"voices": tts_service.available_voices}

@app.post("/tts", response_model=Union[TTSResponse, None])
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize speech from text
    
    Args:
        request: TTS request
        
    Returns:
        Path to audio file or streaming response
    """
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not initialized")
    
    try:
        # Log request details
        logger.debug(f"TTS request: text={request.text[:20]}..., voice={request.voice}, stream={request.stream}")
        
        # Handle streaming
        if request.stream:
            async def generate_audio_stream():
                async for audio_data in tts_service.process_text(
                    text=request.text,
                    voice=request.voice,
                    speed=request.speed,
                    session_id=request.session_id,
                    stream=True
                ):
                    yield audio_data
            
            return StreamingResponse(
                generate_audio_stream(),
                media_type="audio/wav",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": request.session_id or ""
                }
            )
        else:
            # For non-streaming, return a file
            audio_path = await tts_service.process_text(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                session_id=request.session_id,
                stream=False
            )
            
            # Get relative path for URL
            file_name = os.path.basename(audio_path)
            
            return {
                "session_id": request.session_id,
                "audio_url": f"/audio/{file_name}",
                "message": "Audio generated successfully"
            }
            
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{file_name}")
async def get_audio(file_name: str):
    """
    Get generated audio file
    
    Args:
        file_name: Audio file name
        
    Returns:
        Audio file
    """
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not initialized")
    
    file_path = os.path.join(tts_service.cache_dir, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        file_path,
        media_type="audio/wav",
        headers={"Cache-Control": "max-age=3600"}
    )

@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new TTS session
    
    Args:
        request: Session configuration
        
    Returns:
        Session ID
    """
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not initialized")
    
    session_id = tts_service.create_session(voice=request.voice)
    
    return {"session_id": session_id, "message": "Session created"}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get session information
    
    Args:
        session_id: Session ID
        
    Returns:
        Session information
    """
    if tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not initialized")
        
    session_info = tts_service.get_session_info(session_id)
    
    if "error" in session_info:
        raise HTTPException(status_code=404, detail=session_info["error"])
        
    return session_info

# --- Main entry point ---

def main():
    """Run the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TTS API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--voices-dir", type=str, default=None, help="Directory containing voice models")
    parser.add_argument("--lang-code", type=str, default="a", help="Language code for Kokoro")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger("tts_api").setLevel(logging.DEBUG)
    
    # Set environment variables for the app
    if args.voices_dir:
        os.environ["TTS_VOICES_DIR"] = args.voices_dir
    os.environ["TTS_LANG_CODE"] = args.lang_code
    
    # Run the app
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()