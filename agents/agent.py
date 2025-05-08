import os
import asyncio
import logging
import json
import time
import uuid
import websockets
import requests
import wave
import tempfile
import threading
import queue
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator, Union, Tuple
import io
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_agent")

# --- Audio Player ---

class AudioPlayer:
    """Audio playback with non-blocking queue"""
    
    def __init__(self, channels: int = 1, sample_rate: int = 24000):
        """
        Initialize audio player
        
        Args:
            channels: Number of audio channels
            sample_rate: Sample rate
        """
        try:
            import pyaudio
            self.pyaudio_available = True
        except ImportError:
            logger.warning("PyAudio not available. Install with: pip install pyaudio")
            self.pyaudio_available = False
            return
            
        self.channels = channels
        self.sample_rate = sample_rate
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        
        # Queue for audio files to play
        self.audio_queue = queue.Queue()
        
        # Event to signal stop
        self.stop_event = threading.Event()
        
        # Additional flag to track if we're currently playing anything
        self.is_playing = False
        
        # Start playback thread
        self.playback_thread = None
        self.start_playback_thread()
    
    def start_playback_thread(self):
        """Start the background playback thread"""
        if not self.pyaudio_available:
            return
            
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.stop_event.clear()
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                daemon=True
            )
            self.playback_thread.start()
    
    def _playback_worker(self):
        """Worker thread to play audio files in background"""
        while not self.stop_event.is_set():
            try:
                # Get audio file or data with timeout
                audio_item = self.audio_queue.get(timeout=0.1)
                
                if audio_item is None:
                    # None is a signal to stop
                    self.audio_queue.task_done()
                    break
                
                # Mark that we're playing
                self.is_playing = True
                
                # Check if it's a file path or audio data
                if isinstance(audio_item, str):
                    # It's a file path
                    self._play_file_internal(audio_item)
                else:
                    # It's audio data
                    self._play_bytes_internal(audio_item)
                
                # Mark as done
                self.audio_queue.task_done()
                
                # Check if queue is empty
                if self.audio_queue.empty():
                    self.is_playing = False
                
            except queue.Empty:
                # No audio to play, continue waiting
                self.is_playing = False
                continue
            except Exception as e:
                logger.error(f"Error in audio playback: {e}")
                # Mark as done even if there's an error
                try:
                    self.audio_queue.task_done()
                except:
                    pass
                self.is_playing = False
    
    def start_stream(self):
        """Start audio stream for direct byte playback"""
        if not self.pyaudio_available:
            return
            
        if self.stream:
            self.stop_stream()
        
        import pyaudio    
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True
        )
    
    def stop_stream(self):
        """Stop audio stream"""
        if not self.pyaudio_available:
            return
            
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def queue_audio_file(self, file_path: str):
        """
        Queue audio file for playback
        
        Args:
            file_path: Path to audio file
        """
        if not self.pyaudio_available:
            return
            
        self.audio_queue.put(file_path)
    
    def play_bytes(self, audio_data: bytes):
        """
        Queue audio bytes for playback
        
        Args:
            audio_data: Audio data as bytes
        """
        if not self.pyaudio_available:
            return
            
        self.audio_queue.put(audio_data)
    
    def _play_bytes_internal(self, audio_data: bytes):
        """
        Internal method to play audio bytes
        
        Args:
            audio_data: Audio data as bytes
        """
        if not self.pyaudio_available:
            return
            
        if not self.stream:
            self.start_stream()
            
        self.stream.write(audio_data)
    
    def play_file(self, file_path: str):
        """
        Queue audio file for playback
        
        Args:
            file_path: Path to audio file
        """
        if not self.pyaudio_available:
            return
            
        self.queue_audio_file(file_path)
    
    def _play_file_internal(self, file_path: str):
        """
        Internal method to play audio file
        
        Args:
            file_path: Path to audio file
        """
        if not self.pyaudio_available:
            return
            
        try:
            import pyaudio
            # Open the WAV file
            with wave.open(file_path, 'rb') as wf:
                # Get file parameters
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                sample_width = wf.getsampwidth()
                
                # Create stream with file parameters
                stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(sample_width),
                    channels=channels,
                    rate=sample_rate,
                    output=True
                )
                
                # Read and play in chunks
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                
                while data and not self.stop_event.is_set():
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                # Close stream
                stream.stop_stream()
                stream.close()
                
        except Exception as e:
            logger.error(f"Error playing file: {e}")
    
    def wait_for_playback(self, timeout: Optional[float] = None):
        """
        Wait for all queued audio to finish playing
        
        Args:
            timeout: Optional timeout in seconds
        """
        if not self.pyaudio_available:
            return
            
        try:
            self.audio_queue.join()
        except Exception as e:
            logger.error(f"Error waiting for playback: {e}")
    
    def is_audio_playing(self):
        """Check if audio is currently playing"""
        if not self.pyaudio_available:
            return False
        
        return self.is_playing or not self.audio_queue.empty()
    
    def stop(self):
        """Stop playback and clean up resources"""
        if not self.pyaudio_available:
            return
            
        # Signal playback thread to stop
        self.stop_event.set()
        
        # Clear queue
        try:
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
        except:
            pass
        
        # Add None to queue to signal stop
        self.audio_queue.put(None)
        
        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2.0)
        
        # Stop stream
        self.stop_stream()
        
        # Reset flag
        self.is_playing = False
    
    def __del__(self):
        """Clean up resources"""
        self.stop()
        
        if hasattr(self, 'pyaudio') and self.pyaudio:
            self.pyaudio.terminate()

# --- ASR Client ---

class ASRClient:
    """Client for ASR WebSocket server"""
    
    def __init__(self, server_url: str):
        """
        Initialize client
        
        Args:
            server_url: WebSocket server URL
        """
        self.server_url = server_url
        self.websocket = None
        self.stream_id = None
        self.is_connected = False
        self.last_pong_time = 0
        self.last_audio_sent_time = 0
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            # Connect with ping/pong settings to keep connection alive
            # Using shorter timeouts to detect issues faster
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=5,       # Send ping every 5 seconds
                ping_timeout=10,       # Wait 10 seconds for pong response
                close_timeout=5        # Wait 5 seconds for close to complete
            )
            self.is_connected = True
            self.last_pong_time = time.time()
            self.last_audio_sent_time = time.time()
            logger.info(f"Connected to ASR server at {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"ASR connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.is_connected = False
                logger.info("Disconnected from ASR server")
    
    async def start_stream(self, stream_id: Optional[str] = None):
        """Start a new ASR stream"""
        if not self.is_connected:
            logger.error("Not connected to ASR server")
            return None
            
        try:
            # Send start command
            await self.websocket.send(json.dumps({
                'command': 'start',
                'stream_id': stream_id
            }))
            
            # Wait for response
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('status') == 'ok':
                self.stream_id = response_data.get('stream_id')
                logger.info(f"ASR stream started with ID: {self.stream_id}")
                return self.stream_id
            else:
                logger.error(f"Failed to start ASR stream: {response_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting ASR stream: {e}")
            self.is_connected = False
            return None
    
    async def stop_stream(self):
        """Stop current stream"""
        if not self.is_connected or not self.stream_id:
            logger.error("Not connected to ASR server or no active stream")
            return False
            
        try:
            # Send stop command
            await self.websocket.send(json.dumps({
                'command': 'stop'
            }))
            
            # Wait for response (which should be the final transcription)
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            # Process and return the final response
            if response_data.get('type') == 'final':
                logger.info("ASR stream stopped. Final results received.")
                self.stream_id = None
                return response_data
                
            self.stream_id = None
            return True
                
        except Exception as e:
            logger.error(f"Error stopping ASR stream: {e}")
            self.is_connected = False
            return False
    
    async def reset_stream(self):
        """Reset current stream"""
        if not self.is_connected or not self.stream_id:
            logger.error("Not connected to ASR server or no active stream")
            return False
            
        try:
            # Send reset command
            await self.websocket.send(json.dumps({
                'command': 'reset'
            }))
            
            # Wait for response
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('status') == 'ok':
                logger.info("ASR stream reset")
                return True
            else:
                logger.error(f"Failed to reset ASR stream: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Error resetting ASR stream: {e}")
            self.is_connected = False
            return False
    
    async def configure_vad(self, threshold: Optional[float] = None,
                          speech_pad_ms: Optional[int] = None,
                          min_speech_ms: Optional[int] = None,
                          min_silence_ms: Optional[int] = None):
        """Configure VAD parameters"""
        if not self.is_connected or not self.stream_id:
            logger.error("Not connected to ASR server or no active stream")
            return False
            
        try:
            # Build command with only provided parameters
            config = {
                'command': 'configure_vad'
            }
            
            if threshold is not None:
                config['threshold'] = threshold
                
            if speech_pad_ms is not None:
                config['speech_pad_ms'] = speech_pad_ms
                
            if min_speech_ms is not None:
                config['min_speech_ms'] = min_speech_ms
                
            if min_silence_ms is not None:
                config['min_silence_ms'] = min_silence_ms
            
            # Send command
            await self.websocket.send(json.dumps(config))
            
            # Wait for response
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('status') == 'ok':
                logger.info(f"VAD configured successfully")
                return True
            else:
                logger.error(f"Failed to configure VAD: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Error configuring VAD: {e}")
            self.is_connected = False
            return False
    
    async def send_audio_chunk(self, audio_chunk: bytes):
        """Send audio chunk to server"""
        if not self.is_connected:
            logger.error("Not connected to ASR server")
            return False
            
        try:
            # Send binary audio data
            await self.websocket.send(audio_chunk)
            self.last_audio_sent_time = time.time()
            return True
                
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            self.is_connected = False
            return False
    
    async def check_connection(self):
        """Check if connection is alive and try to send a ping"""
        if not self.is_connected:
            return False
            
        try:
            # Try to send a ping to check connection
            pong_waiter = await self.websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=5)
            self.last_pong_time = time.time()
            return True
        except Exception as e:
            logger.error(f"WebSocket ping failed: {e}")
            self.is_connected = False
            return False
    
    async def receive_transcriptions(self, timeout=0.1):
        """
        Check for and process any available transcription messages
        
        Args:
            timeout: How long to wait for a message
            
        Returns:
            Received message or None if no message available
        """
        if not self.is_connected:
            return None
            
        try:
            # Try to receive a message with short timeout
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            response_data = json.loads(response)
            return response_data
        except asyncio.TimeoutError:
            # No message within timeout period
            return None
        except Exception as e:
            logger.error(f"Error receiving transcription: {e}")
            self.is_connected = False
            return None

# --- LLM Client ---

class LLMClient:
    """Client for the LLM API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize client
        
        Args:
            base_url: API base URL
        """
        self.base_url = base_url
        self.session_id = None
        self.http_session = requests.Session()
        
    def create_session(self, system_prompt: Optional[str] = None, knowledge: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            system_prompt: Optional system prompt
            knowledge: Optional knowledge context
            
        Returns:
            Session ID
        """
        url = f"{self.base_url}/sessions"
        data = {}
        
        if system_prompt:
            data["system_prompt"] = system_prompt
            
        if knowledge:
            data["knowledge"] = knowledge
            
        try:
            response = self.http_session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.session_id = result["session_id"]
            
            logger.info(f"Created LLM session: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"Error creating LLM session: {e}")
            return ""
    
    def clear_session(self, session_id: Optional[str] = None) -> bool:
        """
        Clear a session's conversation history
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            Success flag
        """
        session_id = session_id or self.session_id
        
        if not session_id:
            logger.error("No LLM session ID provided or set")
            return False
            
        url = f"{self.base_url}/sessions/{session_id}/clear"
        
        try:
            response = self.http_session.post(url)
            response.raise_for_status()
            logger.info(f"Cleared LLM session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing LLM session: {e}")
            return False
    
    def get_conversation(self, session_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            Conversation history
        """
        session_id = session_id or self.session_id
        
        if not session_id:
            logger.error("No LLM session ID provided or set")
            return []
            
        url = f"{self.base_url}/sessions/{session_id}/conversation"
        
        try:
            response = self.http_session.get(url)
            response.raise_for_status()
            result = response.json()
            return result.get("conversation", [])
        except Exception as e:
            logger.error(f"Error getting LLM conversation: {e}")
            return []
    
    def generate(self, 
               prompt: Optional[str] = None, 
               messages: Optional[List[Dict[str, str]]] = None,
               system_prompt: Optional[str] = None,
               knowledge: Optional[str] = None,
               max_tokens: int = 1024,
               temperature: float = 0.7,
               top_p: float = 0.9,
               session_id: Optional[str] = None,
               stream: bool = False) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate text
        
        Args:
            prompt: Text prompt
            messages: Conversation messages
            system_prompt: System prompt
            knowledge: Additional knowledge context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling probability  
            session_id: Session ID (uses current session if None)
            stream: Whether to stream the response
            
        Returns:
            Generated text or async generator for streaming
        """
        session_id = session_id or self.session_id
        url = f"{self.base_url}/generate"
        
        data = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }
        
        if session_id:
            data["session_id"] = session_id
            
        if prompt:
            data["prompt"] = prompt
            
        if messages:
            data["messages"] = messages
            
        if system_prompt:
            data["system_prompt"] = system_prompt
            
        if knowledge:
            data["knowledge"] = knowledge
        
        if stream:
            # Return async generator for streaming
            return self._stream_generate(url, data)
        else:
            # Regular response
            try:
                response = self.http_session.post(url, json=data)
                response.raise_for_status()
                
                result = response.json()
                return result["text"]
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                return ""
    
    def extract_order(self, session_id: Optional[str] = None, api_key: str = None, 
                     base_url: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract order information from conversation using powerful LLM API
        
        Args:
            session_id: Session ID (uses current session if None)
            api_key: API key for the external LLM service
            base_url: Base URL for the external LLM service
            model: Model to use for extraction
            
        Returns:
            Extracted order information as a dictionary
        """
        session_id = session_id or self.session_id
        
        if not session_id:
            logger.error("No LLM session ID provided or set")
            return {}
            
        if not api_key:
            logger.error("No API key provided for order extraction")
            return {}
            
        url = f"{self.base_url}/extract_order"
        
        data = {
            "session_id": session_id,
            "api_key": api_key
        }
        
        if base_url:
            data["base_url"] = base_url
            
        if model:
            data["model"] = model
        
        try:
            response = self.http_session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully extracted order data")
            return result
        except Exception as e:
            logger.error(f"Error extracting order information: {e}")
            return {}
            
    async def _stream_generate(self, url: str, data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream generator for LLM responses
        
        Args:
            url: API URL
            data: Request data
            
        Yields:
            Text chunks
        """
        # Send request with stream=True to get raw response
        try:
            with self.http_session.post(url, json=data, stream=True) as response:
                response.raise_for_status()
                
                # Read and process server-sent events
                for line in response.iter_lines():
                    if line:
                        # Parse SSE format: lines starting with "data: "
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            chunk = line_text[6:]  # Remove "data: " prefix
                            
                            # Check if it's the end marker
                            if chunk == "[DONE]":
                                break
                            
                            # Yield the chunk
                            yield chunk
        except Exception as e:
            logger.error(f"Error in LLM streaming: {e}")
            yield f"[Error: {str(e)}]"

# --- TTS Client ---

class TTSClient:
    """Client for the TTS API with non-streaming approach"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize client
        
        Args:
            base_url: API base URL
        """
        self.base_url = base_url
        self.session_id = None
        self.http_session = requests.Session()
        
        # Audio playback
        self.audio_player = AudioPlayer()
            
    def list_voices(self) -> List[str]:
        """
        Get list of available voices
        
        Returns:
            List of voice names
        """
        url = f"{self.base_url}/voices"
        
        try:
            response = self.http_session.get(url)
            response.raise_for_status()
            result = response.json()
            return result.get("voices", [])
        except Exception as e:
            logger.error(f"Error getting TTS voices: {e}")
            return []
    
    def create_session(self, voice: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            voice: Voice to use for this session
            
        Returns:
            Session ID
        """
        url = f"{self.base_url}/sessions"
        data = {}
        
        if voice:
            data["voice"] = voice
            
        try:
            response = self.http_session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.session_id = result["session_id"]
            
            logger.info(f"Created TTS session: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"Error creating TTS session: {e}")
            return ""
    
    def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get session information
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            Session information
        """
        session_id = session_id or self.session_id
        
        if not session_id:
            logger.error("No TTS session ID provided or set")
            return {}
            
        url = f"{self.base_url}/sessions/{session_id}"
        
        try:
            response = self.http_session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting TTS session info: {e}")
            return {}
    
    def synthesize(self, 
                 text: str, 
                 voice: Optional[str] = None,
                 speed: float = 1.0,
                 session_id: Optional[str] = None,
                 stream: bool = False,  # This parameter is ignored, always uses non-streaming
                 play_audio: bool = True) -> Optional[str]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed
            session_id: Session ID (uses current session if None)
            stream: Not used, kept for compatibility
            play_audio: Whether to play the audio
            
        Returns:
            Path to audio file
        """
        session_id = session_id or self.session_id
        url = f"{self.base_url}/tts"
        
        data = {
            "text": text,
            "speed": speed,
            "stream": False  # Always use non-streaming for reliability
        }
        
        if voice:
            data["voice"] = voice
            
        if session_id:
            data["session_id"] = session_id
        
        # For non-streaming, we get a URL to the audio file
        try:
            response = self.http_session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            audio_url = result.get("audio_url")
            
            if not audio_url:
                logger.error("No audio URL in TTS response")
                return None
            
            # Download audio file
            audio_path = self._download_audio(audio_url)
            
            # Play audio if requested
            if play_audio and audio_path:
                self.audio_player.play_file(audio_path)
            
            return audio_path
                
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return self.audio_player.is_audio_playing()
    
    def _download_audio(self, audio_url: str) -> Optional[str]:
        """
        Download audio file from URL
        
        Args:
            audio_url: Audio URL
            
        Returns:
            Path to downloaded file
        """
        # Get complete URL
        if audio_url.startswith('/'):
            url = f"{self.base_url}{audio_url}"
        else:
            url = audio_url
        
        try:
            # Download file
            response = self.http_session.get(url, stream=True)
            response.raise_for_status()
            
            # Create temp file
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            
            # Save to file
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
    
    def stop(self):
        """Stop client and clean up resources"""
        if self.audio_player:
            self.audio_player.stop()

# --- Voice Agent Class ---

class VoiceAgent:
    """
    Voice Agent that combines ASR, LLM, and TTS services
    Manages the full conversation flow with real-time streaming
    """
    
    def __init__(self, 
                 agent_id: str,
                 asr_url: str = "ws://localhost:8002/ws",
                 llm_url: str = "http://localhost:8000",
                 tts_url: str = "http://localhost:8001",
                 system_prompt: Optional[str] = None,
                 knowledge: Optional[str] = None,
                 tts_voice: Optional[str] = "af_heart",
                 tts_speed: float = 1.0,
                 vad_config: Optional[Dict[str, Any]] = None,
                 extraction_config: Optional[Dict[str, Any]] = None):
        """
        Initialize voice agent
        
        Args:
            agent_id: Unique identifier for this agent
            asr_url: ASR WebSocket URL
            llm_url: LLM API URL
            tts_url: TTS API URL
            system_prompt: LLM system prompt
            knowledge: Knowledge context for LLM
            tts_voice: TTS voice to use
            tts_speed: TTS speech speed
            vad_config: VAD configuration for ASR
            extraction_config: Configuration for order extraction
        """
        self.agent_id = agent_id
        
        # Initialize clients
        self.asr_client = ASRClient(asr_url)
        self.llm_client = LLMClient(llm_url)
        self.tts_client = TTSClient(tts_url)
        
        # Configuration
        self.system_prompt = system_prompt
        self.knowledge = knowledge
        self.tts_voice = tts_voice
        self.tts_speed = tts_speed
        self.vad_config = vad_config or {}
        self.extraction_config = extraction_config or {}
        
        # State
        self.is_running = False
        self.is_speaking = False
        self.session_started = False
        self.silent_audio_chunk = b'\x00' * 3200  # Default silent chunk
        self.conversation_finished = False
        self.extracted_order = None
        
        # Event to signal stop
        self.stop_event = asyncio.Event()
        
        # Tasks
        self.heartbeat_task = None
        self.keepalive_task = None
        
        # Callbacks
        self.on_transcription = None
        self.on_llm_response = None
        self.on_speaking_started = None
        self.on_speaking_finished = None
        self.on_order_extracted = None
        
        logger.info(f"Voice agent {agent_id} initialized")
    
    async def start(self):
        """Start the agent and initialize all services"""
        logger.info(f"Starting voice agent {self.agent_id}")
        
        # Connect to ASR
        asr_connected = await self.asr_client.connect()
        if not asr_connected:
            logger.error("Failed to connect to ASR service")
            return False
            
        # Create LLM session
        llm_session = self.llm_client.create_session(
            system_prompt=self.system_prompt,
            knowledge=self.knowledge
        )
        if not llm_session:
            logger.error("Failed to create LLM session")
            await self.asr_client.disconnect()
            return False
            
        # Create TTS session
        tts_session = self.tts_client.create_session(
            voice=self.tts_voice
        )
        if not tts_session:
            logger.error("Failed to create TTS session")
            await self.asr_client.disconnect()
            return False
            
        # Start ASR stream
        asr_stream = await self.asr_client.start_stream()
        if not asr_stream:
            logger.error("Failed to start ASR stream")
            await self.asr_client.disconnect()
            return False
            
        # Configure VAD if provided
        if self.vad_config:
            logger.info(f"Configuring VAD for agent {self.agent_id}")
            await self.asr_client.configure_vad(**self.vad_config)
        
        # Start heartbeat task
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Start keepalive task for ASR connection
        self.keepalive_task = asyncio.create_task(self._keepalive_loop())
        
        self.is_running = True
        self.session_started = True
        self.conversation_finished = False
        self.extracted_order = None
        
        logger.info(f"Voice agent {self.agent_id} started successfully")
        
        return True
    
    async def _heartbeat_loop(self):
        """Background task to check and maintain connections"""
        try:
            while not self.stop_event.is_set():
                if self.asr_client.is_connected:
                    # Check connection with ping
                    await self.asr_client.check_connection()
                else:
                    # Try to reconnect
                    if self.is_running:
                        logger.info("ASR connection lost, attempting to reconnect...")
                        await self._reconnect_asr()
                
                # Wait before next heartbeat
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.debug("Heartbeat task cancelled")
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")
    
    async def _keepalive_loop(self):
        """Background task to keep ASR connection alive by sending silent audio"""
        try:
            while not self.stop_event.is_set():
                # Only send keepalive when connected
                if self.asr_client.is_connected:
                    # Check if we need to send a keepalive packet
                    current_time = time.time()
                    time_since_last_audio = current_time - self.asr_client.last_audio_sent_time
                    
                    # Send keepalive every second, especially during speaking
                    if time_since_last_audio > 1.0 or self.is_speaking:
                        await self.asr_client.send_audio_chunk(self.silent_audio_chunk)
                        if self.is_speaking:
                            # During speaking, log less frequently to avoid spam
                            if int(current_time) % 10 == 0:  # Log every 10 seconds
                                logger.debug("Sent keepalive audio chunk during speech")
                        else:
                            logger.debug("Sent keepalive audio chunk (no activity)")
                
                # Small wait to prevent CPU hogging (much shorter during speaking)
                await asyncio.sleep(0.2 if self.is_speaking else 0.5)
        except asyncio.CancelledError:
            logger.debug("Keepalive task cancelled")
        except Exception as e:
            logger.error(f"Error in keepalive loop: {e}")
    
    async def _reconnect_asr(self):
        """Attempt to reconnect to ASR service"""
        # Maximum reconnection attempts
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"ASR reconnection attempt {attempt}/{max_attempts}")
            
            # Try to disconnect cleanly first
            try:
                await self.asr_client.disconnect()
            except:
                pass
            
            # Wait before retry
            await asyncio.sleep(1)
            
            # Try to reconnect
            connected = await self.asr_client.connect()
            if connected:
                # Start a new stream
                stream_id = await self.asr_client.start_stream()
                if stream_id:
                    # Configure VAD if needed
                    if self.vad_config:
                        await self.asr_client.configure_vad(**self.vad_config)
                    
                    logger.info(f"Successfully reconnected to ASR service")
                    return True
            
            # Increase wait time between retries
            await asyncio.sleep(attempt * 2)
        
        logger.error(f"Failed to reconnect to ASR service after {max_attempts} attempts")
        return False
    
    async def stop(self):
        """Stop the agent and clean up resources"""
        logger.info(f"Stopping voice agent {self.agent_id}")
        
        # Set stop event
        self.stop_event.set()
        
        # Cancel background tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.keepalive_task:
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass
        
        # Stop ASR stream
        if self.asr_client.is_connected:
            try:
                await self.asr_client.stop_stream()
            except Exception as e:
                logger.error(f"Error stopping ASR stream: {e}")
            
            await self.asr_client.disconnect()
        
        # Stop TTS client
        self.tts_client.stop()
        
        self.is_running = False
        logger.info(f"Voice agent {self.agent_id} stopped")
        
        # If the conversation is finished but order hasn't been extracted yet, do it now
        if self.conversation_finished and self.extracted_order is None:
            await self.extract_order()
    
    async def finish_conversation(self):
        """
        Mark the conversation as finished and extract order information
        """
        if not self.is_running:
            return
        
        logger.info(f"Finishing conversation for agent {self.agent_id}")
        self.conversation_finished = True
        
        # Extract order information
        await self.extract_order()
    
    async def extract_order(self):
        """
        Extract order information from the conversation using the powerful LLM API
        """
        # Check if extraction config is provided
        if not self.extraction_config or not self.extraction_config.get('api_key'):
            logger.error("No extraction configuration or API key provided")
            return
        
        logger.info(f"Extracting order information for agent {self.agent_id}")
        
        try:
            # Extract order using the LLM API
            order_data = self.llm_client.extract_order(
                api_key=self.extraction_config.get('api_key'),
                base_url=self.extraction_config.get('base_url'),
                model=self.extraction_config.get('model')
            )
            
            # Store the extracted order
            self.extracted_order = order_data
            
            # Log the extracted order
            logger.info(f"Order extracted: {json.dumps(order_data)}")
            
            # Call the callback if provided
            if self.on_order_extracted:
                self.on_order_extracted(order_data)
                
            return order_data
        except Exception as e:
            logger.error(f"Error extracting order: {e}")
            return None
    
    async def process_audio_stream(self, audio_stream):
        """
        Process streaming audio from a source (e.g., microphone)
        
        Args:
            audio_stream: Async generator yielding audio chunks
        """
        if not self.is_running:
            success = await self.start()
            if not success:
                return
        
        # Task for checking transcriptions
        transcription_task = asyncio.create_task(self._check_transcriptions())
        
        try:
            # Initialize silent chunk size
            first_chunk = True
            
            async for audio_chunk in audio_stream:
                if self.stop_event.is_set():
                    break
                
                # Get silent chunk of the same size for the first audio chunk
                if first_chunk:
                    self.silent_audio_chunk = b'\x00' * len(audio_chunk)
                    first_chunk = False
                
                # Check if ASR connection is alive
                if not self.asr_client.is_connected:
                    logger.warning("ASR connection lost during audio processing")
                    await self._reconnect_asr()
                    if not self.asr_client.is_connected:
                        # If reconnection failed, wait a bit and continue
                        await asyncio.sleep(1)
                        continue
                
                # Only send real audio when not speaking
                # (Keepalive task handles silent audio during speaking)
                if not self.is_speaking:
                    # Send actual audio for processing
                    await self.asr_client.send_audio_chunk(audio_chunk)
            
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
        finally:
            # Clean up
            transcription_task.cancel()
            try:
                await transcription_task
            except asyncio.CancelledError:
                pass
            
            # Mark the conversation as finished and extract order if not already done
            if not self.conversation_finished:
                await self.finish_conversation()
    
    async def _check_transcriptions(self):
        """Background task to check for transcriptions"""
        reconnect_attempts = 0
        max_reconnect_attempts = 3
        
        while not self.stop_event.is_set():
            try:
                # Check if we need to reconnect
                if not self.asr_client.is_connected and reconnect_attempts < max_reconnect_attempts:
                    logger.info(f"ASR connection lost, attempting to reconnect ({reconnect_attempts+1}/{max_reconnect_attempts})")
                    reconnect_attempts += 1
                    
                    success = await self._reconnect_asr()
                    if success:
                        reconnect_attempts = 0  # Reset counter
                    else:
                        # Wait before next attempt
                        await asyncio.sleep(2)
                    
                    continue
                
                # Only try to receive messages if connected
                if self.asr_client.is_connected:
                    msg = await self.asr_client.receive_transcriptions(timeout=0.1)
                    
                    # Process message if not speaking
                    if msg and not self.is_speaking:
                        await self._handle_transcription(msg)
                
                # Small sleep to prevent CPU hogging
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error checking transcriptions: {e}")
                await asyncio.sleep(0.1)
    
    async def _handle_transcription(self, message):
        """
        Handle transcription message from ASR
        
        Args:
            message: Transcription message
        """
        if message.get('type') == 'transcription':
            is_final = message.get('is_final', False)
            transcript = message.get('transcript', '')
            
            # Skip empty transcripts
            if not transcript.strip():
                return
            
            # Call the callback if provided
            if self.on_transcription:
                self.on_transcription(transcript, is_final)
            
            # If this is a final transcription, process with LLM
            if is_final:
                logger.info(f"Final transcription: {transcript}")
                asyncio.create_task(self._process_with_llm(transcript))
    
    async def _process_with_llm(self, user_input):
        """
        Process user input with LLM and synthesize response
        
        Args:
            user_input: User input text
        """
        try:
            logger.info(f"Processing with LLM: {user_input}")
            
            # Set speaking flag to prevent processing of self-speech
            self.is_speaking = True
            
            # Generate LLM response with streaming
            full_response = ""
            buffer = ""
            
            async for chunk in self.llm_client._stream_generate(
                f"{self.llm_client.base_url}/generate",
                {
                    "prompt": user_input,
                    "session_id": self.llm_client.session_id,
                    "stream": True,
                    "temperature": 0.15,
                    "top_p": 0.9,
                    "max_tokens": 1024
                }
            ):
                full_response += chunk
                buffer += chunk
                
                # Call the callback if provided
                if self.on_llm_response:
                    self.on_llm_response(chunk, False)
                
                # When buffer contains complete sentence, synthesize it
                sentences = self._split_into_sentences(buffer)
                if len(sentences) > 1:
                    # Synthesize all complete sentences
                    complete_sentences = sentences[:-1]
                    text_to_speak = " ".join(complete_sentences)
                    
                    # Clear spoken text from buffer
                    buffer = sentences[-1]
                    
                    # Synthesize and play in background (non-blocking)
                    if self.on_speaking_started:
                        self.on_speaking_started(text_to_speak)
                    
                    # Use thread for TTS synthesis to avoid blocking
                    await asyncio.to_thread(
                        self.tts_client.synthesize,
                        text_to_speak,
                        self.tts_voice,
                        self.tts_speed,
                        self.tts_client.session_id,
                        False,
                        True
                    )
            
            # Process any remaining text
            if buffer:
                # Synthesize and play remaining text
                if self.on_speaking_started:
                    self.on_speaking_started(buffer)
                
                # Use thread for TTS synthesis
                await asyncio.to_thread(
                    self.tts_client.synthesize,
                    buffer,
                    self.tts_voice,
                    self.tts_speed,
                    self.tts_client.session_id,
                    False,
                    True
                )
            
            # Wait for all audio to finish playing
            while self.tts_client.is_playing():
                # Just wait a bit and check again
                await asyncio.sleep(0.1)
            
            # Call the callback with final response
            if self.on_llm_response:
                self.on_llm_response(full_response, True)
                
            if self.on_speaking_finished:
                self.on_speaking_finished()
            
            # Reset speaking flag
            self.is_speaking = False
            
            # Check if conversation should be ended
            # (This could be determined by various signals in the conversation)
            # For example, if the LLM response contains specific ending phrases:
            if "thank you for your order" in full_response.lower() or \
               "your order is confirmed" in full_response.lower() or \
               "is there anything else you need" in full_response.lower() or \
               "goodbye" in full_response.lower():
                # This is a good time to extract order information
                await self.finish_conversation()
            
        except Exception as e:
            logger.error(f"Error processing with LLM: {e}")
            self.is_speaking = False
    
    def _split_into_sentences(self, text):
        """
        Split text into sentences for smoother TTS
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting - could be improved
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences