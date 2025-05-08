import os
import logging
import uuid
import asyncio
import json
import time
import threading
from typing import Dict, List, Optional, Any, AsyncGenerator, Union, Tuple
import io
from pathlib import Path

import torch
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import NeMo ASR components
import nemo.collections.asr as nemo_asr
from nemo.collections.asr.models.ctc_bpe_models import EncDecCTCModelBPE
from omegaconf import OmegaConf, open_dict
import copy

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to catch all issues
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("asr_api")

# --- Pydantic Models ---

class CreateStreamRequest(BaseModel):
    stream_id: Optional[str] = None

class CreateStreamResponse(BaseModel):
    stream_id: str
    message: str

class VADConfigRequest(BaseModel):
    threshold: Optional[float] = None
    speech_pad_ms: Optional[int] = None
    min_speech_ms: Optional[int] = None
    min_silence_ms: Optional[int] = None

class StreamResponse(BaseModel):
    stream_id: str
    message: str
    status: str = "ok"

class TranscriptionResponse(BaseModel):
    stream_id: str
    is_final: bool
    transcript: str
    all_utterances: Optional[List[str]] = None

# --- Core ASR Classes ---

class VADProcessor:
    """
    Voice Activity Detection for detecting speech segments.
    Uses energy-based detection with state machine logic to accurately
    determine speech boundaries and utterance completion.
    """
    
    def __init__(self, 
                 threshold: float = 0.01, 
                 speech_pad_ms: int = 300,
                 min_speech_duration_ms: int = 100,
                 min_silence_duration_ms: int = 500,
                 sample_rate: int = 16000,
                 max_silence_duration_ms: int = 10000):  # Default 10 seconds max silence
        """
        Initialize VAD processor
        
        Args:
            threshold: Energy threshold for speech detection
            speech_pad_ms: Padding to add after speech ends (ms)
            min_speech_duration_ms: Minimum speech segment duration (ms)
            min_silence_duration_ms: Minimum silence duration to end segment (ms)
            sample_rate: Audio sample rate
            max_silence_duration_ms: Maximum silence duration before forcing utterance end (ms)
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.speech_pad_samples = int(speech_pad_ms * sample_rate / 1000)
        self.min_speech_samples = int(min_speech_duration_ms * sample_rate / 1000)
        self.min_silence_samples = int(min_silence_duration_ms * sample_rate / 1000)
        self.max_silence_samples = int(max_silence_duration_ms * sample_rate / 1000)
        
        # State variables
        self.is_speech = False
        self.silence_count = 0
        self.speech_count = 0
        self.padding_count = 0
        self.in_padding = False
        
        # Debug statistics
        self.debug_stats = {
            "speech_segments": 0,
            "silence_segments": 0,
            "utterance_ends": 0,
            "max_speech_energy": 0.0,
            "min_speech_energy": 1.0,
            "avg_speech_energy": 0.0,
            "speech_energy_samples": 0
        }
    
    def update_energy_stats(self, energy: float, is_speech: bool):
        """Update energy statistics for debugging"""
        if is_speech:
            self.debug_stats["speech_energy_samples"] += 1
            self.debug_stats["avg_speech_energy"] = (
                (self.debug_stats["avg_speech_energy"] * (self.debug_stats["speech_energy_samples"] - 1) + energy) / 
                self.debug_stats["speech_energy_samples"]
            )
            self.debug_stats["max_speech_energy"] = max(self.debug_stats["max_speech_energy"], energy)
            self.debug_stats["min_speech_energy"] = min(self.debug_stats["min_speech_energy"], energy)
        
    def process(self, audio_chunk: np.ndarray) -> Tuple[bool, bool]:
        """
        Process audio chunk and determine if it contains speech
        
        Args:
            audio_chunk: Audio data as numpy array
            
        Returns:
            Tuple of (is_speech, utterance_end)
                is_speech: True if chunk contains speech
                utterance_end: True if this chunk ends an utterance
        """
        # Calculate energy level
        energy = np.mean(np.abs(audio_chunk))
        utterance_end = False
        
        # Check for all-zero input
        if np.all(audio_chunk == 0):
            current_is_speech = False
        else:
            current_is_speech = energy > self.threshold
            
        # Update stats
        self.update_energy_stats(energy, current_is_speech)
        
        # State machine
        if current_is_speech:
            self.debug_stats["speech_segments"] += 1
            
            # Reset silence counter
            self.silence_count = 0
            
            # Increment speech counter
            self.speech_count += len(audio_chunk)
            
            # If we have enough speech, mark as speech
            if self.speech_count >= self.min_speech_samples:
                self.is_speech = True
                
            # Reset padding state
            self.in_padding = False
            self.padding_count = 0
            
        else:  # Not speech
            self.debug_stats["silence_segments"] += 1
            
            # Increment silence counter
            self.silence_count += len(audio_chunk)
            
            # If we were in speech and now have enough silence...
            if self.is_speech:
                if not self.in_padding:
                    # Start padding
                    self.in_padding = True
                    self.padding_count = 0
                
                if self.in_padding:
                    # Update padding counter
                    self.padding_count += len(audio_chunk)
                    
                    # If padding is done and we have enough silence, end utterance
                    if (self.padding_count >= self.speech_pad_samples and 
                        self.silence_count >= self.min_silence_samples):
                        utterance_end = True
                        self.is_speech = False
                        self.speech_count = 0
                        self.silence_count = 0
                        self.padding_count = 0
                        self.in_padding = False
                        self.debug_stats["utterance_ends"] += 1
                    
                    # Force utterance end if silence is very long (failsafe)
                    elif self.silence_count >= self.max_silence_samples:
                        utterance_end = True
                        self.is_speech = False
                        self.speech_count = 0
                        self.silence_count = 0
                        self.padding_count = 0
                        self.in_padding = False
                        self.debug_stats["utterance_ends"] += 1
        
        return self.is_speech, utterance_end
    
    def get_debug_stats(self) -> Dict[str, Any]:
        """Get VAD debug statistics"""
        return self.debug_stats
        
    def reset(self):
        """Reset VAD state"""
        self.is_speech = False
        self.silence_count = 0
        self.speech_count = 0
        self.padding_count = 0
        self.in_padding = False
        
        # Reset stats too
        self.debug_stats = {
            "speech_segments": 0,
            "silence_segments": 0,
            "utterance_ends": 0,
            "max_speech_energy": 0.0,
            "min_speech_energy": 1.0,
            "avg_speech_energy": 0.0,
            "speech_energy_samples": 0
        }

class StreamState:
    """
    Maintains state for a single audio stream including audio buffer,
    VAD state, and transcription history.
    """
    
    def __init__(self, stream_id: str, vad_config: Dict[str, Any] = None):
        """
        Initialize a new stream state
        
        Args:
            stream_id: Unique identifier for this stream
            vad_config: Optional configuration for VAD
        """
        self.stream_id = stream_id
        self.session_id = str(uuid.uuid4())
        
        # Configure VAD with defaults or provided config
        vad_config = vad_config or {}
        self.vad = VADProcessor(
            threshold=vad_config.get('threshold', 0.01),
            speech_pad_ms=vad_config.get('speech_pad_ms', 300),
            min_speech_duration_ms=vad_config.get('min_speech_duration_ms', 100),
            min_silence_duration_ms=vad_config.get('min_silence_duration_ms', 500),
            max_silence_duration_ms=vad_config.get('max_silence_duration_ms', 10000)
        )
        
        # Audio buffer and processing state
        self.audio_buffer = []  # Holds audio chunks during speech
        self.is_speech = False
        self.last_update = time.time()
        
        # Transcription state
        self.intermediate_transcript = ""
        self.final_transcript = ""
        self.completed_utterances = []
        self.is_active = True
        
        # Metrics
        self.speech_duration_seconds = 0.0
        self.total_audio_duration_seconds = 0.0
        self.utterance_count = 0
        self.last_utterance_time = None
        
        # Timestamp for debug purposes
        self.created_at = time.time()
        self.last_utterance_ended_at = None

    def update_last_active(self):
        """Update last activity timestamp"""
        self.last_update = time.time()
        
    def add_audio(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> Tuple[bool, bool, str]:
        """
        Add audio chunk to the stream and process with VAD
        
        Args:
            audio_chunk: Audio data as numpy array
            sample_rate: Sample rate of audio in Hz
            
        Returns:
            Tuple of (is_speech, utterance_end, transcript)
        """
        # Update last active timestamp
        self.update_last_active()
        
        # Update total audio duration
        chunk_duration = len(audio_chunk) / sample_rate
        self.total_audio_duration_seconds += chunk_duration
        
        # Process through VAD
        is_speech, utterance_end = self.vad.process(audio_chunk)
        self.is_speech = is_speech
        
        # If speech, add to buffer
        if is_speech:
            self.audio_buffer.append(audio_chunk)
            self.speech_duration_seconds += chunk_duration
            
        # If utterance ended, update metrics
        if utterance_end:
            self.utterance_count += 1
            self.last_utterance_time = time.time()
            self.last_utterance_ended_at = time.time()
            
        # Return current status
        return is_speech, utterance_end, self.intermediate_transcript
    
    def get_audio_buffer(self) -> np.ndarray:
        """Get concatenated audio buffer"""
        if not self.audio_buffer:
            return np.array([], dtype=np.float32)
        return np.concatenate(self.audio_buffer)
    
    def clear_audio_buffer(self):
        """Clear audio buffer"""
        self.audio_buffer = []
    
    def add_completed_utterance(self, transcript: str):
        """Add a completed utterance to the history"""
        if transcript and transcript.strip():  # Only add non-empty transcripts
            self.completed_utterances.append(transcript)
            self.final_transcript = transcript
    
    def get_state_dict(self) -> Dict[str, Any]:
        """Get a dictionary representation of the stream state"""
        return {
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "is_speech": self.is_speech,
            "last_update": self.last_update,
            "intermediate_transcript": self.intermediate_transcript,
            "final_transcript": self.final_transcript,
            "completed_utterances": self.completed_utterances,
            "is_active": self.is_active,
            "speech_duration_seconds": self.speech_duration_seconds,
            "total_audio_duration_seconds": self.total_audio_duration_seconds,
            "utterance_count": self.utterance_count,
            "last_utterance_time": self.last_utterance_time,
            "vad_stats": self.vad.get_debug_stats()
        }
    
    def reset(self):
        """Reset stream state but keep the same IDs"""
        self.vad.reset()
        self.audio_buffer = []
        self.is_speech = False
        self.intermediate_transcript = ""
        self.final_transcript = ""
        self.update_last_active()

class ASRService:
    """
    Central ASR service that handles multiple streams
    Uses a single model instance that's shared across all streams
    """
    
    def __init__(self, 
                model_name: str = "stt_en_fastconformer_hybrid_large_streaming_multi",
                lookahead_size: int = 80,
                decoder_type: str = "rnnt",
                session_timeout_sec: int = 300):
        """
        Initialize the ASR service
        
        Args:
            model_name: NeMo model name to use
            lookahead_size: Lookahead size in milliseconds
            decoder_type: Decoder type ("rnnt" or "ctc")
            session_timeout_sec: Session timeout in seconds
        """
        logger.info(f"Initializing ASR Service with model {model_name}")
        
        self.session_timeout_sec = session_timeout_sec
        
        # Initialize model
        self.model = self._init_model(model_name, lookahead_size, decoder_type)
        self.preprocessor = self._init_preprocessor()
        
        # Streams storage
        self.streams = {}
        self.streams_lock = threading.RLock()
            
        # Start session cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def _init_model(self, model_name, lookahead_size, decoder_type):
        """Initialize the ASR model"""
        model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)
        
        # Set up model for streaming with proper lookahead
        if model_name == "stt_en_fastconformer_hybrid_large_streaming_multi":
            if lookahead_size not in [0, 80, 480, 1040]:
                raise ValueError(f"Invalid lookahead_size: {lookahead_size}")
            
            # Update attention context size
            left_context_size = model.encoder.att_context_size[0]
            model.encoder.set_default_att_context_size(
                [left_context_size, int(lookahead_size / 80)]  # 80ms is the encoder step
            )
        
        # Configure decoder and decoding strategy
        model.change_decoding_strategy(decoder_type=decoder_type)
        decoding_cfg = model.cfg.decoding
        with open_dict(decoding_cfg):
            decoding_cfg.strategy = "greedy"
            decoding_cfg.preserve_alignments = False
            if hasattr(model, 'joint'):  # if an RNNT model
                decoding_cfg.greedy.max_symbols = 10
                decoding_cfg.fused_batch_size = -1
            model.change_decoding_strategy(decoding_cfg)
        
        # Set model to eval mode
        model.eval()
        return model
    
    def _init_preprocessor(self):
        """Initialize audio preprocessor"""
        cfg = copy.deepcopy(self.model._cfg)
        OmegaConf.set_struct(cfg.preprocessor, False)
        cfg.preprocessor.dither = 0.0
        cfg.preprocessor.pad_to = 0
        cfg.preprocessor.normalize = "None"
        
        preprocessor = EncDecCTCModelBPE.from_config_dict(cfg.preprocessor)
        preprocessor.to(self.model.device)
        
        return preprocessor
    
    def _cleanup_sessions(self):
        """Background thread to clean up inactive sessions"""
        while True:
            try:
                # Sleep for a bit to avoid excessive checking
                time.sleep(30)
                
                current_time = time.time()
                to_remove = []
                
                with self.streams_lock:
                    for stream_id, stream in self.streams.items():
                        if (current_time - stream.last_update) > self.session_timeout_sec:
                            to_remove.append(stream_id)
                    
                    # Remove inactive streams
                    for stream_id in to_remove:
                        logger.info(f"Removing inactive stream {stream_id}")
                        del self.streams[stream_id]
                        
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    def create_stream(self, stream_id: Optional[str] = None) -> str:
        """
        Create a new stream for audio processing
        
        Args:
            stream_id: Optional stream ID, will generate one if not provided
            
        Returns:
            Stream ID
        """
        if stream_id is None:
            stream_id = str(uuid.uuid4())
            
        with self.streams_lock:
            if stream_id in self.streams:
                logger.warning(f"Stream {stream_id} already exists, resetting it")
                self.streams[stream_id].reset()
            else:
                logger.info(f"Creating new stream {stream_id}")
                self.streams[stream_id] = StreamState(stream_id)
                
        return stream_id
    
    def delete_stream(self, stream_id: str) -> bool:
        """
        Delete a stream
        
        Args:
            stream_id: Stream ID to delete
            
        Returns:
            True if successful, False if stream not found
        """
        with self.streams_lock:
            if stream_id in self.streams:
                logger.info(f"Deleting stream {stream_id}")
                del self.streams[stream_id]
                return True
            return False
    
    def reset_stream(self, stream_id: str) -> bool:
        """
        Reset a stream to start fresh
        
        Args:
            stream_id: Stream ID to reset
            
        Returns:
            True if successful, False if stream not found
        """
        with self.streams_lock:
            if stream_id in self.streams:
                logger.info(f"Resetting stream {stream_id}")
                self.streams[stream_id].reset()
                return True
            return False
    
    def configure_vad(self, stream_id: str, threshold: float = None,
                      speech_pad_ms: int = None, min_speech_ms: int = None,
                      min_silence_ms: int = None) -> Dict[str, Any]:
        """
        Configure VAD parameters for a stream
        
        Args:
            stream_id: Stream ID to configure
            threshold: Energy threshold for speech detection
            speech_pad_ms: Padding to add after speech ends (ms)
            min_speech_ms: Minimum speech segment duration (ms)
            min_silence_ms: Minimum silence duration to end segment (ms)
            
        Returns:
            Dict with status information
        """
        with self.streams_lock:
            # Check if stream exists
            if stream_id not in self.streams:
                return {"error": f"Stream {stream_id} not found"}
                
            stream = self.streams[stream_id]
            
            # Update VAD parameters
            if threshold is not None:
                stream.vad.threshold = threshold
                logger.info(f"VAD threshold set to {threshold} for stream {stream_id}")
                
            if speech_pad_ms is not None:
                stream.vad.speech_pad_samples = int(speech_pad_ms * stream.vad.sample_rate / 1000)
                logger.info(f"VAD speech pad set to {speech_pad_ms}ms for stream {stream_id}")
                
            if min_speech_ms is not None:
                stream.vad.min_speech_samples = int(min_speech_ms * stream.vad.sample_rate / 1000)
                logger.info(f"VAD min speech duration set to {min_speech_ms}ms for stream {stream_id}")
                
            if min_silence_ms is not None:
                stream.vad.min_silence_samples = int(min_silence_ms * stream.vad.sample_rate / 1000)
                logger.info(f"VAD min silence duration set to {min_silence_ms}ms for stream {stream_id}")
        
        return {
            "status": "ok",
            "stream_id": stream_id,
            "message": "VAD parameters updated"
        }
    
    def _extract_transcription(self, hypotheses):
        """Extract text from ASR hypotheses"""
        if not hypotheses:
            return ""
            
        # Handle different hypothesis formats
        if hasattr(hypotheses[0], "text"):
            return hypotheses[0].text
        elif isinstance(hypotheses[0], list) and hypotheses[0] and hasattr(hypotheses[0][0], "text"):
            return hypotheses[0][0].text
        else:
            return str(hypotheses[0])
    
    def process_audio(self, stream_id: str, audio_bytes: bytes, 
                    sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Process a chunk of audio for a stream
        
        Args:
            stream_id: Stream ID to process
            audio_bytes: Audio chunk as bytes (16-bit PCM)
            sample_rate: Sample rate of audio
            
        Returns:
            Dict with status and transcription information
        """
        with self.streams_lock:
            # Check if stream exists
            if stream_id not in self.streams:
                logger.warning(f"Stream {stream_id} not found, creating new stream")
                self.create_stream(stream_id)
                
            stream = self.streams[stream_id]
                
        # Convert bytes to numpy array
        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return {
                "stream_id": stream_id,
                "error": f"Invalid audio data: {e}",
                "is_speech": False,
                "utterance_end": False,
                "transcript": "",
                "is_final": False
            }
            
        # Process through VAD
        is_speech, utterance_end, current_transcript = stream.add_audio(audio_np, sample_rate)
        
        # Always process with ASR if we have collected speech data
        audio_buffer = stream.get_audio_buffer()
        
        if len(audio_buffer) > 0:
            # Process with ASR
            try:
                with torch.no_grad():
                    # Preprocess audio
                    audio_tensor = torch.from_numpy(audio_buffer).unsqueeze(0).to(self.model.device)
                    audio_len = torch.tensor([len(audio_buffer)], device=self.model.device)
                    
                    processed_signal, processed_signal_length = self.preprocessor(
                        input_signal=audio_tensor, length=audio_len
                    )
                    
                    # Run model inference
                    model_output = self.model(
                        processed_signal=processed_signal,
                        processed_signal_length=processed_signal_length
                    )
                    
                    # Get transcription
                    hypotheses = self.model.decoding.rnnt_decoder_predictions_tensor(
                        model_output[0], model_output[1]
                    ) if hasattr(self.model.decoding, 'rnnt_decoder_predictions_tensor') else self.model.decoding(
                        model_output[0], model_output[1]
                    )
                    
                    transcript = self._extract_transcription(hypotheses)
                    
                    # Update stream state
                    if utterance_end:
                        # Only add non-empty transcripts to completed utterances
                        if transcript.strip():
                            stream.add_completed_utterance(transcript)
                        
                        # Clear buffer after final transcription
                        stream.clear_audio_buffer()
                        logger.info(f"Utterance completed for stream {stream_id}. Final: '{transcript}'")
                    else:
                        stream.intermediate_transcript = transcript
                        
            except Exception as e:
                logger.error(f"Error in ASR processing: {e}")
                return {
                    "stream_id": stream_id,
                    "error": f"ASR processing error: {e}",
                    "is_speech": is_speech,
                    "utterance_end": utterance_end,
                    "transcript": stream.intermediate_transcript,
                    "is_final": False
                }
        
        # Return the current state
        return {
            "stream_id": stream_id,
            "is_speech": is_speech,
            "utterance_end": utterance_end,
            "transcript": stream.final_transcript if utterance_end else stream.intermediate_transcript,
            "is_final": utterance_end,
            "all_utterances": stream.completed_utterances
        }

    def get_stream_state(self, stream_id: str) -> Dict[str, Any]:
        """
        Get current state of a stream
        
        Args:
            stream_id: Stream ID to query
            
        Returns:
            Dict with stream state or error
        """
        with self.streams_lock:
            if stream_id not in self.streams:
                return {"error": f"Stream {stream_id} not found"}
                
            stream = self.streams[stream_id]
            
            return {
                "stream_id": stream_id,
                "session_id": stream.session_id,
                "is_speech": stream.is_speech,
                "last_update": stream.last_update,
                "intermediate_transcript": stream.intermediate_transcript,
                "final_transcript": stream.final_transcript,
                "completed_utterances": stream.completed_utterances,
                "is_active": stream.is_active
            }

# --- FastAPI App ---

app = FastAPI(
    title="ASR API",
    description="API for speech recognition with VAD and streaming support",
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

# Global ASR service instance
asr_service = None

# Track connected websocket clients
connected_clients = {}

@app.on_event("startup")
async def startup_event():
    """Initialize ASR service on startup"""
    global asr_service
    # Get model config from environment or use defaults
    model_name = os.environ.get("ASR_MODEL", "stt_en_fastconformer_hybrid_large_streaming_multi")
    lookahead_size = int(os.environ.get("ASR_LOOKAHEAD", "80"))
    decoder_type = os.environ.get("ASR_DECODER", "rnnt")
    timeout = int(os.environ.get("ASR_SESSION_TIMEOUT", "300"))
    
    # Initialize service
    asr_service = ASRService(
        model_name=model_name,
        lookahead_size=lookahead_size,
        decoder_type=decoder_type,
        session_timeout_sec=timeout
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "ASR API is running"}

@app.post("/streams", response_model=CreateStreamResponse)
async def create_stream(request: CreateStreamRequest):
    """
    Create a new ASR stream
    
    Args:
        request: Stream creation request
        
    Returns:
        Stream ID and status
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    stream_id = asr_service.create_stream(request.stream_id)
    
    return {
        "stream_id": stream_id,
        "message": "Stream created"
    }

@app.delete("/streams/{stream_id}", response_model=StreamResponse)
async def delete_stream(stream_id: str):
    """
    Delete an ASR stream
    
    Args:
        stream_id: Stream ID to delete
        
    Returns:
        Status message
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    success = asr_service.delete_stream(stream_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")
    
    return {
        "stream_id": stream_id,
        "message": "Stream deleted",
        "status": "ok"
    }

@app.post("/streams/{stream_id}/reset", response_model=StreamResponse)
async def reset_stream(stream_id: str):
    """
    Reset an ASR stream
    
    Args:
        stream_id: Stream ID to reset
        
    Returns:
        Status message
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    success = asr_service.reset_stream(stream_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")
    
    return {
        "stream_id": stream_id,
        "message": "Stream reset",
        "status": "ok"
    }

@app.post("/streams/{stream_id}/vad", response_model=StreamResponse)
async def configure_vad(stream_id: str, config: VADConfigRequest):
    """
    Configure VAD for a stream
    
    Args:
        stream_id: Stream ID to configure
        config: VAD configuration
        
    Returns:
        Status message
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    result = asr_service.configure_vad(
        stream_id,
        threshold=config.threshold,
        speech_pad_ms=config.speech_pad_ms,
        min_speech_ms=config.min_speech_ms,
        min_silence_ms=config.min_silence_ms
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {
        "stream_id": stream_id,
        "message": "VAD configured",
        "status": "ok"
    }

@app.get("/streams/{stream_id}")
async def get_stream_state(stream_id: str):
    """
    Get current state of a stream
    
    Args:
        stream_id: Stream ID to query
        
    Returns:
        Stream state
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    state = asr_service.get_stream_state(stream_id)
    
    if "error" in state:
        raise HTTPException(status_code=404, detail=state["error"])
    
    return state

@app.post("/streams/{stream_id}/audio")
async def process_audio(stream_id: str, request: Request):
    """
    Process audio for a stream (binary data in request body)
    
    Args:
        stream_id: Stream ID to process
        request: Request with binary audio data
        
    Returns:
        Transcription results
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    # Read binary audio data from request body
    audio_bytes = await request.body()
    
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio data")
    
    # Process audio
    result = asr_service.process_audio(stream_id, audio_bytes)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming audio and control commands
    
    Args:
        websocket: WebSocket connection
    """
    if asr_service is None:
        await websocket.close(code=1013, reason="ASR service not initialized")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Store client information (we'll set the stream ID when the client requests one)
    client_id = str(uuid.uuid4())
    connected_clients[client_id] = {
        "websocket": websocket,
        "stream_id": None
    }
    
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Main connection loop
        while True:
            # First, try to receive a message for commands
            try:
                # Check if the client is still connected before receiving
                message = await websocket.receive()
                
                # Check if this is a disconnect message
                if message.get("type") == "websocket.disconnect":
                    logger.info(f"Received disconnect message from client {client_id}")
                    break
                
                if "text" in message:
                    # Handle text message (commands)
                    text = message["text"]
                    try:
                        command = json.loads(text)
                        cmd_type = command.get("command", "")
                        logger.debug(f"Received command: {cmd_type}")
                        
                        if cmd_type == "start":
                            # Start new stream
                            stream_id = command.get("stream_id")
                            stream_id = asr_service.create_stream(stream_id)
                            connected_clients[client_id]["stream_id"] = stream_id
                            
                            await websocket.send_json({
                                "type": "control",
                                "status": "ok", 
                                "stream_id": stream_id
                            })
                            logger.info(f"Started stream {stream_id} for client {client_id}")
                            
                        elif cmd_type == "stop":
                            # Stop current stream
                            stream_id = connected_clients[client_id].get("stream_id")
                            if stream_id:
                                state = asr_service.get_stream_state(stream_id)
                                
                                await websocket.send_json({
                                    "type": "final",
                                    "stream_id": stream_id,
                                    "transcription": state 
                                })
                                
                                asr_service.delete_stream(stream_id)
                                connected_clients[client_id]["stream_id"] = None
                                logger.info(f"Stopped stream {stream_id}")
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "No active stream"
                                })
                                
                        elif cmd_type == "reset":
                            # Reset stream
                            stream_id = connected_clients[client_id].get("stream_id")
                            if stream_id:
                                asr_service.reset_stream(stream_id)
                                await websocket.send_json({
                                    "type": "control",
                                    "status": "ok",
                                    "message": "Stream reset"
                                })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "No active stream"
                                })
                                
                        elif cmd_type == "configure_vad":
                            # Configure VAD
                            stream_id = connected_clients[client_id].get("stream_id")
                            if stream_id:
                                result = asr_service.configure_vad(
                                    stream_id,
                                    threshold=command.get("threshold"),
                                    speech_pad_ms=command.get("speech_pad_ms"),
                                    min_speech_ms=command.get("min_speech_ms"),
                                    min_silence_ms=command.get("min_silence_ms")
                                )
                                
                                if "error" in result:
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": result["error"]
                                    })
                                else:
                                    await websocket.send_json({
                                        "type": "control",
                                        "status": "ok",
                                        "message": "VAD configured"
                                    })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "No active stream"
                                })
                                
                        elif cmd_type == "get_state":
                            # Get stream state
                            stream_id = connected_clients[client_id].get("stream_id")
                            if stream_id:
                                state = asr_service.get_stream_state(stream_id)
                                await websocket.send_json({
                                    "type": "state",
                                    "stream_id": stream_id,
                                    "state": state
                                })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "No active stream"
                                })
                                
                        else:
                            # Unknown command
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Unknown command: {cmd_type}"
                            })
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON: {text}")
                        await websocket.send_json({
                            "type": "error", 
                            "message": "Invalid JSON command"
                        })
                
                elif "bytes" in message:
                    # Handle binary message (audio data)
                    audio_bytes = message["bytes"]
                    logger.debug(f"Received audio chunk: {len(audio_bytes)} bytes")
                    
                    # Get or create stream
                    stream_id = connected_clients[client_id].get("stream_id")
                    if not stream_id:
                        stream_id = asr_service.create_stream()
                        connected_clients[client_id]["stream_id"] = stream_id
                        logger.info(f"Auto-created stream {stream_id} for client {client_id}")
                    
                    # Process audio
                    result = asr_service.process_audio(stream_id, audio_bytes)
                    
                    if "error" in result:
                        await websocket.send_json({
                            "type": "error",
                            "message": result["error"]
                        })
                    else:
                        # Send transcription result
                        if result.get("utterance_end", False):
                            await websocket.send_json({
                                "type": "transcription",
                                "stream_id": stream_id,
                                "is_final": True,
                                "transcript": result.get("transcript", ""),
                                "all_utterances": result.get("all_utterances", [])
                            })
                        else:
                            await websocket.send_json({
                                "type": "transcription",
                                "stream_id": stream_id,
                                "is_final": False,
                                "transcript": result.get("transcript", "")
                            })
            except WebSocketDisconnect:
                # Client disconnected
                logger.info(f"Client {client_id} disconnected")
                break
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
    finally:
        # Clean up
        stream_id = connected_clients[client_id].get("stream_id") if client_id in connected_clients else None
        if stream_id:
            logger.info(f"Deleting stream {stream_id}")
            asr_service.delete_stream(stream_id)
            
        if client_id in connected_clients:
            del connected_clients[client_id]
            
        logger.info(f"Cleaned up resources for client {client_id}")

@app.websocket("/ws/audio/{stream_id}")
async def websocket_audio_endpoint(websocket: WebSocket, stream_id: str):
    """
    WebSocket endpoint specifically for audio streaming with a predefined stream ID
    
    Args:
        websocket: WebSocket connection
        stream_id: Stream ID to use
    """
    if asr_service is None:
        await websocket.close(code=1013, reason="ASR service not initialized")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Create or get stream
    if "error" in asr_service.get_stream_state(stream_id):
        stream_id = asr_service.create_stream(stream_id)
    
    # Store client
    client_id = str(uuid.uuid4())
    connected_clients[client_id] = {
        "websocket": websocket,
        "stream_id": stream_id
    }
    
    logger.info(f"Client {client_id} connected to audio stream {stream_id}")
    
    # Send confirmation
    await websocket.send_json({
        "type": "control",
        "status": "ok",
        "stream_id": stream_id,
        "message": "Connected to audio stream"
    })
    
    try:
        # Process audio chunks
        while True:
            try:
                # Receive binary data
                message = await websocket.receive()
                
                if "bytes" in message:
                    audio_bytes = message["bytes"]
                    logger.debug(f"Received audio chunk: {len(audio_bytes)} bytes")
                    
                    # Process audio
                    result = asr_service.process_audio(stream_id, audio_bytes)
                    
                    # Send back results
                    if result.get("utterance_end", False):
                        await websocket.send_json({
                            "type": "transcription",
                            "stream_id": stream_id,
                            "is_final": True,
                            "transcript": result.get("transcript", ""),
                            "all_utterances": result.get("all_utterances", [])
                        })
                    else:
                        await websocket.send_json({
                            "type": "transcription",
                            "stream_id": stream_id,
                            "is_final": False,
                            "transcript": result.get("transcript", "")
                        })
                # Ignore text messages on this endpoint
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected from audio stream")
                break
                
    except Exception as e:
        logger.error(f"Error in audio websocket: {str(e)}")
    finally:
        # Cleanup (but don't delete the stream as it might be shared)
        if client_id in connected_clients:
            del connected_clients[client_id]
        
        logger.info(f"Cleaned up client {client_id}")

# --- Main entry point ---

def main():
    """Run the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ASR API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind to")
    parser.add_argument("--model", type=str, default="stt_en_fastconformer_hybrid_large_streaming_multi", 
                        help="NeMo model to use")
    parser.add_argument("--lookahead", type=int, default=80, help="Lookahead size in ms")
    parser.add_argument("--decoder", type=str, default="rnnt", help="Decoder type (rnnt or ctc)")
    parser.add_argument("--timeout", type=int, default=300, help="Session timeout in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger("asr_api").setLevel(logging.DEBUG)
    
    # Set environment variables for the app
    os.environ["ASR_MODEL"] = args.model
    os.environ["ASR_LOOKAHEAD"] = str(args.lookahead)
    os.environ["ASR_DECODER"] = args.decoder
    os.environ["ASR_SESSION_TIMEOUT"] = str(args.timeout)
    
    # Run the app
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()